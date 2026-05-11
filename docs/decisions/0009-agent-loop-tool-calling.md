# ADR 0009: agent-loop-tool-calling

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Agent **basit tool-calling döngüsü** ile çalışır: LLM tool
> çağırırsa dispatcher uygular, sonuç mesajlara eklenir, LLM tekrar çağrılır;
> tool çağrısı kalmayınca cevap döner. **Max 8 iterasyon** sınırı; aşılırsa
> `AgentLoopExceededError`. Tool definitions tek dosyada (`agent/tools/definitions.py`),
> dispatcher **registry pattern** (`dict[str, Callable]`). İlk tool seti
> **8 tool** (stok, sipariş, kargo, bildirim, tedarikçi taslağı için). Sistem
> promptu `agent/prompts/*.md` markdown dosyalarından yüklenir. Conversation
> state **tek-turlu** — bir `/ai-chat` çağrısı süresince loop hafızasında
> yaşar, çağrı sonunda atılır; iki çağrı arasında geçmiş yok. Agent **RAG
> yapmaz**: structured veriye **self-augmenting tool calling** ile erişir.
>
> **Kapsam:** `src/agent/loop.py`, `src/agent/tools/`, `src/agent/conversation.py`,
> `src/agent/prompts/`. Hem reaktif chat (`/ai-chat`) hem proaktif workflow
> (`morning_briefing`, ADR-0007) aynı `loop.run()` API'sini kullanır.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **Loop sonsuz çalışmaz.** `MAX_TOOL_ITERATIONS = 8`; aşılırsa
>   `AgentLoopExceededError` fırlar, üst katman kullanıcıya anlamlı mesaj
>   döner.
> - **Tool argümanları her çağrıda JSON Schema ile pre-validate edilir.**
>   Schema ihlali bir tool result hatasına dönüşür (sonsuz döngüden
>   korunmak için iterasyon sayar).
> - **Tool exception'ları üst katmana sızmaz.** Dispatcher exception'ı tool
>   result olarak modele döner; model kullanıcıya açıklar. İstisna:
>   `LLMRateLimitError` (ADR-0005) ve `AgentLoopExceededError` üst katmana
>   propagate olur.
> - **Conversation state truncate yasak** (ADR-0005 kuralının uygulaması):
>   reasoning blokları, tool_calls, `reasoning_details` loop içinde tam
>   saklanır.
> - **`/ai-chat` iki çağrısı arasında geçmiş paylaşılmaz** (stateless across
>   requests). Multi-turn chat ihtiyacı doğarsa ayrı ADR.
> - **Yeni tool eklemek = `definitions.py`'a JSON schema + `registry.py`'a
>   callable bağlama + birim test.** Magic dekoratör yok, otomatik discovery
>   yok.
> - **Sistem promptları kod sabiti değildir** — `agent/prompts/*.md`'den
>   yüklenir. Prompt değişimi kod review'a girer ama deploy gerektirmez
>   (varsayım: dosya read-only mount edilmez).
> - **Vektör DB / embedding / semantik arama yasak.** `vectors.db` kalıntısı
>   bu ADR ile silinir; RAG ihtiyacı doğarsa ayrı ADR açılır.

## Context

ADR-0002 agent katmanını kendi parçalarımızla (`loop`, `tools/registry`,
`tools/dispatcher`, `conversation`) konumlandırdı; ADR-0004 LangChain'i yasak
etti; ADR-0005 reasoning_details truncate yasağını koydu; ADR-0007
`morning_briefing` workflow'unu aynı loop'a bağladı; ADR-0008 notifier
adapter'larını kurdu. Şimdi **loop'un içsel davranışı** — iterasyon kuralı,
argüman validasyonu, hata akışı, conversation scope, prompt yönetimi —
yazılı olmazsa kod kararsız davranışa açık kalır.

Mevcut durum:
- `main.py`'da `/ai-chat` basit tek-turlu MiniMax çağrısı; tool calling yok,
  iterasyon yok, validation yok.
- `vectors.db` dosyası repoda var ama hiçbir yerden kullanılmıyor — eski bir
  RAG denemesi kalıntısı.
- Domain language karışıklığı potansiyeli: "RAG mi yapıyoruz?" sorusu
  kullanıcı tarafından açıkça gündeme geldi; cevap **hayır**, ama ADR'da
  netleşmemiş.

Gereksinim: Loop davranışı **deterministik, test edilebilir, sınırları
yazılı** olmalı. Aynı API hem reaktif chat hem proaktif workflow için
çalışmalı. Tool ekleme süreci açık ve disiplinli olmalı.

## Decision

### 1. Pattern: Basit tool-calling döngüsü

Loop'un mantığı (psödokod):

```python
async def run(
    messages: list[Message],
    tools: list[ToolDefinition],
    *,
    system_prompt: str,
    max_iterations: int = 8,
) -> LLMResponse:
    conversation = Conversation(system_prompt=system_prompt, messages=messages)

    for iteration in range(max_iterations):
        response = await llm_client.chat(
            messages=conversation.as_provider_messages(),
            tools=tools,
        )
        conversation.append_assistant(response)  # reasoning + tool_calls KORUNUR

        if not response.tool_calls:
            return response

        for tool_call in response.tool_calls:
            tool_result = await dispatcher.execute(tool_call)
            conversation.append_tool_result(tool_call.id, tool_result)

    raise AgentLoopExceededError(max_iterations)
```

ReAct prompt formatı kullanılmaz; modern LLM tool calling API'si reasoning +
acting'i zaten destekliyor.

### 2. Max iteration limiti

- Sabit: `MAX_TOOL_ITERATIONS = 8` — `Settings`'te override edilebilir
  (dev'de debug için artırılabilir).
- Aşılırsa `AgentLoopExceededError(iterations=8, last_response=...)`
  fırlatılır.
- Üst katman (presentation `/ai-chat` route) bu hatayı yakalar ve kullanıcıya
  Türkçe anlamlı bir mesaj döner:
  `"İsteğinizi tam çözemedim, biraz daha spesifik sorabilir misiniz?"`

### 3. Tool definitions: tek dosya, JSON schema dict listesi

`src/agent/tools/definitions.py`:

```python
TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_product_stock",
        description="Bir ürünün güncel stok miktarını döner. "
                    "Kullanıcı belirli bir ürünün stoğunu sorduğunda kullan.",
        parameters_schema={
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "Ürün adı (örn. 'Domates')"},
            },
            "required": ["product_name"],
        },
    ),
    # ... 7 tool daha
]
```

- Tek dosya, IDE'de aranabilir.
- Açıklamalar **Türkçe** çünkü LLM aynı dili konuşacak; "kullanıcı şunu
  sorduğunda kullan" gibi davranış ipuçları açıklamada yer alır.
- Otomatik dekoratör tabanlı discovery yok (LangChain anti-pattern'i).

### 4. Dispatcher: registry pattern

`src/agent/tools/registry.py`:

```python
ToolHandler = Callable[[dict[str, Any]], Awaitable[ToolResult]]


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None: ...
    def get(self, name: str) -> ToolHandler | None: ...
```

`src/agent/tools/dispatcher.py`:

```python
class ToolDispatcher:
    def __init__(self, registry: ToolRegistry, definitions: list[ToolDefinition]) -> None: ...

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        handler = self._registry.get(tool_call.name)
        if handler is None:
            return ToolResult.error(f"Bilinmeyen tool: {tool_call.name}")

        validation_error = self._validate(tool_call.name, tool_call.arguments)
        if validation_error:
            return ToolResult.error(f"Argüman hatası: {validation_error}")

        try:
            return await handler(tool_call.arguments)
        except Exception as exc:  # noqa: BLE001 — model'e geri ver
            return ToolResult.error(f"Tool yürütme hatası: {exc}")
```

Registry composition root'ta doldurulur:

```python
registry.register("get_product_stock",
    lambda args: stock_service_get_handler(stock_service, args))
```

### 5. İlk tool seti (8 tool)

| Tool | Açıklama | Application Service |
|------|----------|---------------------|
| `get_product_stock(product_name: str)` | Ürün stoğunu döner | `StockService.get_by_name` |
| `list_low_stock_products()` | Eşik altı ürünleri listeler | `StockService.find_below_threshold` |
| `get_order_status(order_id: int)` | Sipariş durumunu döner | `OrderService.get_status` |
| `list_orders(status: str?, date: str?, customer_name: str?)` | Filtreli sipariş listesi | `OrderService.list` |
| `get_shipment_status(order_id: int)` | Kargo durumu + konum + ETA | `ShippingService.get_by_order` |
| `list_delayed_shipments()` | Gecikmiş kargoları listeler | `ShippingService.find_delayed` |
| `notify_customer(order_id: int, message: str)` | Müşteriye bildirim gönderir | `NotificationService.notify_customer` |
| `create_reorder_draft(product_id: int, quantity: int)` | Tedarikçiye taslak sipariş hazırlar | `StockService.create_reorder_draft` |

Tüm tool'lar **read-mostly veya kontrollü write**. Tehlikeli aksiyonlar
(sipariş silme, fiyat değişimi, müşteri verisi silme) tool olarak verilmez.

`notify_customer` ve `create_reorder_draft` write aksiyon yapar; üst
business kural (cooldown, eşik) application service içinde uygulanır
(adapter saf kanal — ADR-0008).

### 6. Sistem promptu yapısı

Klasör: `src/agent/prompts/`

- `system_chat.md` — `/ai-chat` reaktif chat için sistem promptu
- `system_morning_briefing.md` — proaktif sabah özeti workflow için

Yükleme: `prompt_loader.load("system_chat")` → markdown dosyasını okur,
string döner. Composition root'ta loop'a verilir.

Template değişkenleri **şu sürümde yok**; düz markdown. İhtiyaç doğarsa
Jinja2 entegrasyonu ayrı ADR.

Prompt içeriği şunları içerir (her iki dosya için ortak):

- Kim olduğun (rol)
- Domain bağlamı (kooperatif/KOBİ, Türkçe)
- Tool kullanım davranışı (gereksiz tool çağrısı yapma, emin değilsen sor)
- Hata davranışı (tool hata dönerse kullanıcıya açıkla, deneme yapma)
- Çıktı stili (kısa, Türkçe, profesyonel)

### 7. Conversation scope: tek-turlu (per-request)

- Loop **bir** `loop.run(...)` çağrısı süresince conversation tutar.
- Çağrı sonunda dönen `LLMResponse` cevap olarak kullanılır, ardından
  `conversation` nesnesi atılır (Python GC).
- `/ai-chat` endpoint'i **her HTTP isteğinde temiz başlar**; geçmiş yok.
- Bu, ADR-0005'in reasoning_details kuralını basitleştirir (state tek-mesaj
  scope'lu, persist edilmiyor).
- Multi-turn chat (session bazlı geçmiş) gerekirse:
  - `ChatSessionRepository` portu eklenir
  - `/ai-chat` request'ine `session_id` parametresi eklenir
  - DB'de mesaj geçmişi saklanır
  - Bu ayrı bir ADR konusudur (örn. ADR-001X).

### 8. Conversation state semantiği (reasoning preservation)

`src/agent/conversation.py`:

```python
class Conversation:
    def __init__(self, system_prompt: str, messages: list[Message]) -> None: ...

    def append_assistant(self, response: LLMResponse) -> None:
        """Modelin TAM yanıtını ekler — reasoning, tool_calls, text, reasoning_details."""

    def append_tool_result(self, tool_call_id: str, result: ToolResult) -> None: ...

    def as_provider_messages(self) -> list[Message]:
        """LLMClient'a verilecek mesaj listesini döner. Truncation YASAK."""
```

ADR-0005 kuralları: hiçbir alan truncate edilmez; MiniMax M2.7 `<think>`
blokları korunur; OpenAI `reasoning_details` korunur.

### 9. Workflow ile ortak API

`morning_briefing` (ADR-0007) aynı API'yi kullanır:

```python
async def run_morning_briefing(deps: WorkflowDeps) -> str:
    structured_data = await deps.gather_morning_data()
    user_message = build_briefing_request(structured_data)
    response = await deps.agent_loop.run(
        messages=[Message.user(user_message)],
        tools=deps.briefing_tools,
        system_prompt=load_prompt("system_morning_briefing"),
    )
    return response.text
```

Workflow'un kendisi `agent/workflows/morning_briefing.py`'de yaşar; loop
çağrısı sadece bir adım.

### 10. Agent self-augmenting reasoning (RAG değil)

Bu agent **RAG yapmaz**; vektör DB, embedding, semantik benzerlik araması
içermez. Bunun yerine **tool calling ile self-augmenting reasoning**
uygular: LLM kullanıcı sorusunu parçalarına ayırır, her parça için hangi
structured veriye ihtiyaç olduğuna kendisi karar verir, tool çağrılarıyla
bilgiyi adım adım toplar, sonra sentezler.

Tipik akış örneği — *"Ayşe'nin domatesleri nerede?"* sorusu:

1. LLM `list_orders(customer_name="Ayşe")` çağırır → Ayşe'nin siparişlerini
   görür.
2. Domates içeren siparişi tespit eder, `get_shipment_status(order_id=103)`
   çağırır → kargo durumunu görür.
3. Sentezlenmiş Türkçe cevap üretir:
   *"Ayşe'nin domates siparişi (#103) MNG kargoda, İstanbul Avcılar dağıtım
   merkezinde, yarın teslim bekleniyor."*

Bu desen RAG'a göre **dinamik** (LLM ne çekeceğine kendisi karar verir) ve
**çok turlu** (gerekirse `MAX_TOOL_ITERATIONS` sınırına kadar planlama
yapabilir). RAG **statik** ve **tek turlu** (semantic search → sistem
promptuna enjekte → tek cevap).

Hangi araç hangi probleme uygun:

| İhtiyaç | Tool calling | RAG |
|---------|--------------|-----|
| Structured veri sorgusu (DB, API) | ✅ | ❌ |
| Aksiyon alma (bildirim, sipariş) | ✅ | ❌ |
| Çok adımlı planlama | ✅ | ❌ |
| Uzun unstructured döküman (SSS, policy) | ⚠️ | ✅ |
| Semantik benzerlik arama | ❌ | ✅ |

Bizim 5 tema (ADR-0001) hep structured veri üzerinde çalıştığı için tool
calling doğru araç. PDF'in "bilgi sunan değil işlem yapan sistem"
vurgusuyla da bu desen birebir uyumlu. `vectors.db` dosyası bu projede
**kullanılmaz**; Open item olarak silinir.

### 11. Guardrails / Policy

Hackathon kapsamında **yumuşak policy**:
- Business kurallar (cooldown, eşik, write-yetki) zaten application
  service içinde.
- Tool dispatcher seviyesinde ek policy katmanı yok.
- Demo'da agent yetkisi olmayan bir şey yapamaz çünkü tool seti
  sınırlandırılmıştır.

Open item: production'da formal policy katmanı (`agent/policy.py`)
eklenebilir; bu ADR'ı superseded etmeden uygulamayı genişletir.

### 12. Test stratejisi

ADR-0002 test stratejisinin agent için somutlaşması:

- **`FakeLLMClient`**: scripted yanıtlar kuyruğu. Test başlangıcında "şu
  user mesajına şu tool_call dön, sonra şu cevap dön" diye programlanır.
  `tests/_fakes/fake_llm_client.py`.
- **`InMemoryToolRegistry`**: registry'i fake handler'lar ile doldurmak
  test helper'ı.
- **Loop birim testleri** (`tests/unit/agent/`):
  - Happy path: 1 tool çağrısı + cevap
  - Multi-tool: 2-3 tool çağrısı zincirleme + cevap
  - Max iteration aşımı → `AgentLoopExceededError`
  - Tool exception → tool result olarak hata, LLM cevabı
  - Unknown tool → tool result hatası
  - Argüman validation hatası → tool result hatası
- **Dispatcher birim testleri**: registry, validation, exception capture.
- **Conversation birim testleri**: reasoning_details preservation,
  truncate yasağının test edilmesi (regression için).
- **E2E** (`tests/e2e/api/test_ai_chat.py`): FastAPI TestClient + override
  edilmiş `LLMClient` (FakeLLMClient). Gerçek LLM çağrısı yok.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **ReAct prompt format** | Modern tool calling API'leri reasoning + acting'i native destekliyor; ReAct'in promptta "Thought/Action/Observation" zorlaması overhead. |
| **Plan-then-Execute** | Tek-turlu reaktif chat için aşırı; sabah workflow için bile tek-turlu yeterli. Karmaşık görev gelirse ayrı ADR. |
| **Max iteration 5** | Tema 1+2+3 birleşik sorularda ("Ayşe'nin domatesleri nerede?") 3-4 tur lazım; 5 dar sınır. 8 makul güvenli marj. |
| **Max iteration 15** | Sonsuza yaklaşan loop'tan korunma; 15 çok büyük, kullanıcıyı bekletir, LLM cost arttırır. 8 yeterli. |
| **`@tool` dekoratör + otomatik discovery** | LangChain anti-pattern'i; magic, test edilmesi zor, ADR-0004 ruhu ile çelişir. Explicit registry daha iyi. |
| **Tool definitions her tool için ayrı dosya** | 8 tool için 8 dosya overkill; tek dosyada okumak ve diff'lemek daha kolay. İleride 20+ tool olursa yeniden organize edilir. |
| **Sistem promptu kod sabiti** | Prompt iteration sıklığı yüksek; dosya tabanlı yönetim daha çevik. Markdown editor desteği bonus. |
| **Multi-turn chat (session bazlı geçmiş)** | Hackathon kapsamı dar; tek-turlu reaktif chat PDF örnek senaryolarına yetiyor. Session yönetimi (auth, expiry, persist) ayrı ADR. |
| **RAG ile hibrit (tool calling + vector retrieval)** | 5 tema structured veri odaklı; RAG'ın ekleyeceği değer marjinal. Ekstra bağımlılık (chromadb/qdrant), embedding maliyeti, complexity getirir. Önce demo, sonra ihtiyaç doğarsa ayrı ADR. |
| **Formal policy katmanı (RBAC, capabilities)** | Application service'lerinde business kural zaten var. Hackathon demo'da yetki ihtiyacı yok. Production gerekirse eklenir. |
| **Argument validation atlanır, LLM'e güven** | Modern LLM'ler argümanları çoğu zaman doğru üretir ama %5 hata oranı bile demo'yu kırar. Pre-validate ucuz sigorta. |
| **Tool exception üst katmana propagate** | Demo akışını kırar; LLM kullanıcıya bağlamlı bir cevap üretemez. Tool result olarak geri vermek model'in akıllı davranmasına izin verir. |

## Consequences

### Olumlu

- **Deterministik davranış** — iteration sınırı, validation, exception
  capture hepsi yazılı; loop'un nasıl davranacağı testlerle doğrulanabilir.
- **Test edilebilirlik mükemmel** — FakeLLMClient + InMemoryRegistry ile
  loop tamamen API key'siz, hızlı, paralel test edilebilir.
- **Tek API, iki use case** — `loop.run(...)` hem reaktif chat hem
  proaktif workflow için aynı; sürdürülebilirlik kazanımı yüksek.
- **Tool genişletme süreci açık** — yeni tool eklemek 3 adım (definition,
  handler register, test); checklist olarak öğretilebilir.
- **RAG kafa karışıklığı yazıyla çözüldü** — `vectors.db` kalıntısı
  temizlenir; gelecek katılımcılar "burada RAG mi var?" sorusunu ADR'dan
  cevaplar.
- **Demo hikâyesi güçlü** — "Ayşe'nin domatesleri nerede?" gibi 3-4 tool
  çağıran sorular **self-augmenting reasoning**'i jüriye gösterir.

### Olumsuz

- **8 iterasyon sınırı bazen yetmeyebilir** — kompleks sorularda (5+
  zincirleme tool) `AgentLoopExceededError` görülebilir. Karşılığında
  kullanıcıya anlamlı mesaj döner; sınır `Settings`'ten ayarlanır.
- **Tek-turlu conversation** — kullanıcı "az önce sorduğum müşterinin
  diğer siparişleri neydi?" diyemez (geçmiş yok). Hackathon demo'da bu
  vurgulu istenmiyor; ihtiyaç doğarsa ayrı ADR.
- **Prompt dosyaları runtime read** — restart'ta okunur, hot-reload yok.
  Dev iteration hızlı değil; karşılığında basitlik kazanılıyor.
- **Tool seti büyüdükçe definitions.py uzar** — 20+ tool'da dosyayı
  kategorilere bölmek gerekecek; yeni alt-klasör (`tools/definitions/`)
  ile yapılır, ADR superseded gerekmez.
- **RAG yasağı** Müşteri SSS / policy gibi ileride doğabilecek metinsel
  ihtiyaçlar için yeniden ADR açmayı gerektirecek. Kabul edilebilir
  trade-off; hackathon kapsamında ihtiyaç yok.

## Open items

- [ ] `src/agent/loop.py` — `AgentLoop.run(...)` implementasyonu, iteration
      sınırı, exception akışı.
- [ ] `src/agent/conversation.py` — `Conversation` sınıfı, reasoning
      preservation testleri ile birlikte.
- [ ] `src/agent/tools/definitions.py` — 8 tool'un JSON schema'ları,
      Türkçe açıklamalar.
- [ ] `src/agent/tools/registry.py` — `ToolRegistry`.
- [ ] `src/agent/tools/dispatcher.py` — `ToolDispatcher` + JSON Schema
      validator (kütüphane: `jsonschema` veya pydantic ile sınırlı
      kullanım — pydantic adapter sınırında olduğu için kabul).
- [ ] `src/agent/prompts/system_chat.md` ve `system_morning_briefing.md`.
- [ ] `src/agent/prompt_loader.py` — dosyadan markdown okur, string döner.
- [ ] `tests/_fakes/fake_llm_client.py` — scripted yanıtlar.
- [ ] Loop birim testleri (yukarıdaki 6 senaryo).
- [ ] Dispatcher + Conversation birim testleri.
- [ ] E2E `/ai-chat` testi (FakeLLMClient ile).
- [ ] `vectors.db` dosyasını sil, `.gitignore`'a ekle (RAG kalıntısı
      temizliği).
- [ ] Demo akış senaryosunu README'ye yaz (ADR-0001'in Open item'ı):
      "Ayşe'nin domatesleri nerede?" örnek konuşması, jüri için.
- [ ] `Settings`: `max_tool_iterations` (default 8), `prompt_dir`
      (default `agent/prompts`).
- [ ] `MAX_TOOL_ITERATIONS` aşıldığında üst katmanın döneceği Türkçe
      mesaj template'i.

## Affected areas

- `src/agent/` — tüm alt klasörler (loop, tools, prompts, conversation,
  prompt_loader, workflows).
- `src/application/ports/llm_client.py` — `Message`, `ToolDefinition`,
  `ToolCall`, `LLMResponse`, `ToolResult` dataclass'ları ADR-0005'le
  birlikte tanımlı; bu ADR onları kullanır.
- `src/presentation/api/routes/chat.py` — `/ai-chat` endpoint'i, loop
  çağrısı + `AgentLoopExceededError` Türkçe mesaja çevrimi.
- `src/presentation/main.py` — composition root: registry doldurma, loop
  bağlama, prompt_loader DI.
- `static/` veya gelecek frontend — `/ai-chat` cevabını render eder.
- `vectors.db` — silinir (RAG kalıntısı, kullanılmıyor).
- [[0001-hackathon-kapsami-temalar]] — bu ADR Tema 1'in (müşteri iletişim
  agent'ı) kalbidir.
- [[0002-mimari-yaklasim-layered-agent]] — bu ADR oradaki agent
  katmanının iç davranışını somutlaştırır.
- [[0004-agent-cercevesi-langchain-langgraph-kullanilmamasi]] — bu ADR
  "kendi loop'umuzu yazıyoruz" kararının nasıl yazılacağıdır.
- [[0005-llm-saglayici-secimi-minimax-gemini]] — bu ADR oradaki
  reasoning_details preservation kuralını conversation state seviyesinde
  uygular.
- [[0007-scheduler-apscheduler-async]] — `morning_briefing` workflow bu
  ADR'ın `loop.run(...)` API'sini kullanır.
- [[0008-notifier-telegram-frontend-sse]] — `notify_customer` tool'u bu
  ADR'da tanımlanır, oradaki Notifier port'unu çağırır.
- _gelecek ADR_ — Frontend (askıda), multi-turn chat (ihtiyaç doğarsa),
  RAG (ihtiyaç doğarsa) bu ADR'ı superseded etmeden genişletecek.
