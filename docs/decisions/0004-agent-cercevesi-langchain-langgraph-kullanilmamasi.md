# ADR 0004: agent-cercevesi-langchain-langgraph-kullanilmamasi

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Proje, agent katmanında **LangChain ve LangGraph kullanmaz**. Agent
> loop'u, tool registry'si, tool dispatcher'ı ve conversation state yönetimi
> projenin kendi kodu olarak `src/agent/` altında yazılır. LLM sağlayıcılarına
> erişim, sağlayıcıların **resmi Python SDK'ları** (örn. `anthropic`,
> `openai`, MiniMax HTTP) ile `src/infrastructure/llm/` altındaki
> adapter'larda implement edilir; üst katmanlar yalnızca
> `application/ports/llm_client.py` port'unu görür.
>
> **Kapsam:** Tüm agent ve LLM erişim kodu. Bu ADR, ADR-0002'deki agent
> katmanı kararının somut framework karşılığıdır.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - `langchain`, `langchain-core`, `langchain-community`, `langgraph` ve
>   `langchain-*` ile başlayan **hiçbir paket** üretim bağımlılığına eklenemez.
> - LLM sağlayıcısının SDK'sı **yalnızca `src/infrastructure/llm/` içinde**
>   import edilir. `agent/`, `application/`, `domain/`, `presentation/`
>   içinde sağlayıcı SDK'sı import yasak.
> - Agent loop, tool registry, dispatcher gibi "agent kavramları" üçüncü taraf
>   bir framework'e devredilemez; ADR-0002'deki klasör yapısında **kendi
>   kodumuz** olarak yaşar.
> - Sağlayıcı değiştirmek (örn. MiniMax → Claude), yalnızca yeni bir adapter
>   (`infrastructure/llm/<saglayici>_client.py`) yazıp composition root'ta
>   bağlamak demektir. Üst katmanlar değişmez.

## Context

ADR-0002 ile agent **kendi katmanı** olarak konumlandırıldı; loop, registry,
dispatcher, conversation state yedi parçaya ayrıldı ve her parça net dosyalara
yerleştirildi. Test stratejisi de "agent fake `LLMClient` ile scripted
conversation testleri" üzerine kuruldu.

Bu noktada doğal soru: Bu işin büyük bölümünü **LangChain** ve özellikle
**LangGraph** zaten yapmıyor mu? Kullanırsak kod azalmaz mı?

Cevap iki yönlü. **Evet**, LangChain'in `AgentExecutor`'ı veya LangGraph'ın
state graph'ı bizim loop'umuzu yazma gereksinimini kaldırır. **Hayır**, çünkü:

1. **Mimari çelişki:** LangChain'in agent abstraction'ı opinionated bir
   "agent" modeli dayatır. Bizim `agent/tools/registry.py`,
   `agent/loop.py`, `agent/conversation.py` ayrımı LangChain modelinde
   `AgentExecutor`'ın iç meselelerine karışır. ADR-0002'nin "agent katmanı
   kendi parçalarımızla yaşar" kararı sessizce iptal olur.

2. **Test edilebilirlik:** ADR-0002 test stratejisi `FakeLLMClient` ile
   scripted conversation üzerine kuruldu — agent davranışı **API key olmadan,
   deterministik** test edilecek. LangChain `AgentExecutor`'ı kolayca
   script'lenmiyor; LangChain mock'lamak `langchain_core.messages` ve
   `BaseChatModel` arayüzlerini öğrenmeyi gerektirir, kırılgan testler doğurur.
   LangGraph node'ları daha test-dostu ama framework'ün kendi serialize/state
   modeline bağlanır.

3. **Versiyon kırılganlığı:** LangChain `0.0.x` → `0.1.x` → `0.2.x` → `0.3.x`
   breaking change'leri çok sık. Hackathon kodunun bir ay sonra çalışıp
   çalışmayacağı belirsiz. Kendi kodumuz LLM SDK'sının kırılmadığı sürece
   sabittir; SDK kırılırsa **bir adapter** değişir, agent değişmez.

4. **Ekosistem değer önerisinin çoğu kullanılmayacak:** LangChain'in en güçlü
   yanı geniş ekosistem (vector store, retriever, document loader, çok
   sayıda chain). Tema 1-2-3-4-5 kapsamında bu özelliklerin **hiçbiri
   zorunlu değil**. RAG bile şu an kapsamda yok.

5. **LangGraph için durum daha nüanslı:** Tema 5 (sabah workflow) çok-adımlı,
   conditional, retry'lı bir state machine'e dönüşürse LangGraph net fayda
   sağlar. Ancak hackathon kapsamındaki workflow muhtemelen 4-5 lineer adım
   olacak (analiz → kritik tespit → taslak üret → yöneticiye gönder). Bu
   ölçek için düz Python fonksiyonu LangGraph'tan daha iyi okunur, daha iyi
   test edilir.

6. **"Magic" abstraction'ın bedeli:** LangChain debug ederken stack trace
   karmaşık; "neden bu tool çağrıldı?" sorusunun cevabı framework iç
   detayında. Kendi kodumuzla, debug doğrudan bizim modüllerimize gider.

7. **Hackathon kapsamında "büyük proje gibi disiplinli" yazım hedefi** (ADR-0001
   ve kullanıcı tercihi): LangChain'in opinionated modeli "disiplinli yazım"
   yerine "framework yolunu izleme" anlamına gelir. Disiplin için kendi
   sınırlarımızı çizmek daha doğru.

Acı noktası: LangChain'i "biraz kullanalım" diyerek yarı önlem almak en kötüsü.
Yarı kullanım = hem LangChain'in karmaşıklığı hem kendi kodumuzun bakımı —
ikisinden de tam fayda yok, ikisinin de maliyeti var. Bu nedenle karar **net**
olmalı: **hayır**.

## Decision

### 1. LangChain ailesinin tüm paketleri yasak

Üretim bağımlılığında **`langchain*`** ile başlayan hiçbir paket yer almaz.
Test bağımlılığında da yasak. Bu yasak `pyproject.toml`'da ve CI'da
(`import-linter` veya basit grep) doğrulanır.

### 2. LangGraph'ın yasaklanması

LangGraph LangChain ailesinin parçasıdır ve aynı yasak kapsamındadır.
**İstisna kapısı:** Eğer ileride Tema 4+5'in proaktif workflow'u gerçekten
çok-adımlı, conditional, retry'lı, persistent-state'li bir state machine'e
dönüşürse — bu durumda **bu ADR superseded yapılır**, yeni bir ADR (örn.
"ADR-00NN: Proaktif workflow için LangGraph kullanımı") açılır ve LangGraph
**sadece `src/agent/workflows/` altında**, sadece o özel kullanım için
eklenir. Bu istisna önceden açılmaz; ihtiyaç netleştiğinde değerlendirilir.

### 3. LLM SDK seçimi (sağlayıcıya göre)

LLM sağlayıcısının resmi SDK'sı veya doğrudan HTTP (`httpx`) kullanılır:

- **Anthropic Claude için:** `anthropic` resmi Python SDK.
- **OpenAI için:** `openai` resmi Python SDK.
- **MiniMax için:** Resmi Python SDK yoksa `httpx` ile doğrudan HTTP (mevcut
  `main.py`'da olduğu gibi).
- **Diğer sağlayıcılar:** Resmi SDK varsa o; yoksa `httpx` ile HTTP.

Hangi sağlayıcının seçileceği **bu ADR'ın konusu değildir** (ADR-0005 veya
sonrası karar verecek). Bu ADR yalnızca **agent çerçevesi olarak LangChain
kullanılmayacağını** ve sağlayıcı erişiminin nereden yapılacağını sabitler.

### 4. Sağlayıcı SDK'larının sızıntı sınırı

Yukarıdaki SDK'lar yalnızca `src/infrastructure/llm/` altındaki adapter
dosyalarında import edilir. Diğer katmanlar (`domain/`, `application/`,
`agent/`, `presentation/`) **sağlayıcı SDK'sını import edemez**.

Üst katmanlar yalnızca `application/ports/llm_client.py`'deki port arayüzünü
görür. Port, sağlayıcıdan bağımsız dataclass'lar döner (`LLMResponse`,
`ToolCall`, `Message` gibi — `domain` veya `application` modüllerinde
tanımlı).

### 5. Sağlayıcı değiştirme prosedürü

MiniMax → Claude geçişi şu adımlardan ibarettir:

1. `src/infrastructure/llm/claude_client.py` yaz; `LLMClient` port'unu
   `anthropic` SDK ile implement et.
2. `src/presentation/main.py` composition root'unda `LLMClient` bağlamasını
   `MiniMaxClient`'tan `ClaudeClient`'a değiştir.
3. `.env` ve `Settings` config'inde API key alanını değiştir.
4. Üst katmanlarda **tek satır kod değişmez**.

Bu prosedürün doğruluğunun kanıtı: agent ve application testleri **hiç
değişmeden geçmeye devam etmelidir**.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **LangChain'i tam agent framework olarak kullanmak (`AgentExecutor`, `@tool`)** | ADR-0002'nin kendi agent katmanı kararını sessizce iptal eder. Test deterministikliği zorlaşır. Versiyon kırılganlığı hackathon zaman çizelgesi için risk. |
| **LangChain'i sadece LLM adapter olarak kullanmak (sağlayıcı taşınabilirliği)** | Bizim port (`LLMClient`) zaten taşınabilirliği sağlıyor. LangChain'i bu iş için katmak, kullanılmayacak büyük bir bağımlılık ağacı çekmek demektir. Direkt SDK + kendi port daha temiz. |
| **LangGraph'ı tüm agent için kullanmak** | Reaktif sorgu agent'ı (Tema 1) çoğunlukla tek-iki turluk; graph fazla. Ayrıca LangChain ekosistemine bağımlılık aynı şekilde geçerli. |
| **LangGraph'ı yalnızca proaktif workflow için kullanmak (önceden)** | Workflow'un gerçekten çok-adımlı olup olmayacağı henüz belirsiz. YAGNI: önce düz Python fonksiyonu ile başla; karmaşıklaşırsa bu ADR'ı superseded yap. |
| **`Instructor` veya `outlines` gibi structured-output kütüphaneleri** | Şu an structured output ihtiyacımız tool calling ile karşılanıyor; ek bir kütüphaneye gerek yok. Gelecek bir ADR'ın konusu olabilir. |
| **Kendi tüm yığını yazmak ama HTTP'yi de elle yapmak (SDK'sız)** | Sağlayıcının kimlik doğrulama, retry, streaming gibi detaylarını yeniden yazmak gereksiz; resmi SDK varsa onu kullanmak hem doğru hem hızlı. |

## Consequences

### Olumlu

- Agent katmanı **tamamen bizim**; davranış değiştirmek dosya değiştirmek
  kadar şeffaf. Üçüncü taraf "magic" yok.
- Test stratejisi (ADR-0002) sorunsuz çalışır: `FakeLLMClient` ile scripted
  conversation'lar deterministik, hızlı, API key gerektirmiyor.
- Versiyon kırılganlığı düşer; LangChain breaking change'leri bizi etkilemez.
- Sağlayıcı değiştirmek bir adapter işidir; hackathon sırasında MiniMax'tan
  Claude'a geçmek istesek üst katmanlara dokunmadan yapılır.
- `pyproject.toml` bağımlılık ağacı küçük kalır; çakışma riski düşer.
- Sunumda "kendi agent katmanımızı temiz mimari ilkelerine göre yazdık"
  hikâyesi LangChain kullanmaya göre **daha güçlü teknik anlatım**.

### Olumsuz

- Multi-step ReAct, retry, planner gibi gelişmiş pattern'ler ihtiyaç olursa
  bunları kendimiz yazmak zorundayız (LangChain bu pattern'leri hazır
  sunuyordu). Karşılığında bizim ihtiyaç bu kadar yüksek değil; basit
  tool-calling loop yeterli.
- LangGraph'ın graph görselleştirme, checkpoint, replay gibi gelişmiş
  yetenekleri kapı dışında kalıyor. Proaktif workflow karmaşıklaşırsa
  bu kararı yeniden açmak gerekecek.
- Vector store / RAG ihtiyacı doğarsa LangChain'in retriever ekosistemini
  kullanamayız; doğrudan vektör DB SDK'sı (örn. `chromadb`, `qdrant-client`)
  ile yazmak gerekir. Hackathon kapsamında RAG yok, bu yüzden şu an risk değil.
- Topluluk örneklerinin çoğu LangChain merkezli; Stack Overflow'da "kendi
  loop'umla agent yazıyorum" örnekleri daha az. Bu, ilk birkaç saat öğrenme
  sürtünmesi getirir.

## Open items

- [ ] `pyproject.toml`'da `langchain*` ve `langgraph` paketlerinin **yasaklı
      bağımlılık** olarak listelendiği yere bir yorum satırı veya `tool.uv`
      benzeri kısıtlama (varsa) eklemek. Net hatırlatma için CI'da bu paketlerin
      `pip list`'te bulunmadığını doğrulayan basit bir check yazmak.
- [ ] `application/ports/llm_client.py` port arayüzünü taslakla: `chat()`,
      `chat_with_tools()`, `Message`, `ToolCall`, `LLMResponse` dataclass'ları.
- [ ] İlk LLM adapter'ı: mevcut MiniMax çağrısını `infrastructure/llm/minimax_client.py`'ye taşı; port'u implement et.
- [ ] `agent/loop.py` iskeleti: "LLM çağır → tool call varsa dispatcher'a yolla → tool sonucunu mesajlara ekle → tekrar et" döngüsü.
- [ ] `agent/tools/registry.py` ve `dispatcher.py` iskeleti.
- [ ] `agent/conversation.py`: mesaj geçmişi + sistem prompt yönetimi.
- [ ] `FakeLLMClient` test yardımcısı: `tests/unit/agent/conftest.py`.

## Affected areas

- `src/agent/` — bu katmanın tüm parçaları bu ADR'ın somut karşılığı.
- `src/infrastructure/llm/` — sağlayıcı adapter'ları burada yaşayacak.
- `src/application/ports/llm_client.py` — port arayüzü; üst katmanların gördüğü tek LLM yüzeyi.
- `pyproject.toml` — LangChain ailesi paketlerinin yasaklı olduğu yer.
- [[0002-mimari-yaklasim-layered-agent]] — bu ADR oradaki "agent katmanı" kararının somut framework cevabıdır.
- [[0003-cerceve-teknoloji-yigini]] — bu ADR oradaki yığına LLM SDK'larını ekler.
- _gelecek ADR'lar_ — sağlayıcı seçimi (ADR-0005?) ve agent loop pattern'i (multi-step ReAct? planner?) ayrı ADR'larda konuşulacak.
