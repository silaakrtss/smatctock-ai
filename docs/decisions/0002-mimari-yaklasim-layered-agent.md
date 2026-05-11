# ADR 0002: mimari-yaklasim-layered-agent

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Proje **`src/` köklü, dört katmanlı (domain / application / agent /
> infrastructure) + presentation** bir yapıda yazılır. Agent **kendi katmanıdır**;
> application service'lerini "tool" olarak çağırır. Bağımlılık yönü tek
> yönlüdür: `presentation → agent → application → domain`; `infrastructure`
> application'da tanımlı port'ları implement eder.
>
> **Kapsam:** Tüm proje kodu. Mevcut tek dosyalık `main.py` bu ADR ile birlikte
> `src/` altına dağıtılır.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **Clean Code ve SOLID ihlali kesin olarak yasaktır.** Tüm aşağıdaki maddeler
>   bu şemsiyenin altındadır; ayrıca `~/.claude/rules/clean-code.md` ve `clean-code`
>   skill'i her kod değişikliğinde bağlayıcıdır.
> - **Bağımlılık yönü ihlali yasak:** `domain/` içinde FastAPI, SQLAlchemy, httpx,
>   LLM SDK veya başka herhangi bir framework/IO import edilemez.
> - **Soyutlama ihlali yasak:** `application/` içinde concrete adapter (DB, HTTP,
>   LLM) import edilemez; yalnızca kendi tanımladığı port arayüzlerini kullanır.
> - **Sızıntı ihlali yasak:** `agent/` katmanı DB veya HTTP'ye doğrudan dokunamaz;
>   application service'leri üzerinden gider. LLM erişimi
>   `application/ports/llm_client.py` port'u üzerindendir.
> - **DI ihlali yasak:** `presentation/` tek **composition root**'tur — DI burada
>   kurulur, başka hiçbir yerde concrete sınıf `new`/instantiate edilmez.
> - **Boyut ihlali yasak:** Fonksiyon ≤ 20 satır, sınıf/modül ≤ 200 satır,
>   parametre sayısı ≤ 3 (4+ → parameter object).
> - **İsimlendirme ihlali yasak:** Niyet açıklayan isimler zorunlu; `data`, `tmp`,
>   `flag` gibi anlamsız isimler ve magic number'lar yasak.
> - **YAGNI ihlali yasak:** Birden fazla agent için erken organizasyon yapılmaz;
>   `agent/` düz başlar. Hipotetik gereksinim için abstraction kurulmaz.
> - **Test borcu yasak:** Yeni kod testsiz commit edilmez; TDD disiplini
>   (kırmızı → yeşil → refactor) zorunludur.

## Context

ADR-0001 ile beş tema iddiası kabul edildi ve kodun "büyük proje gibi
disiplinli" yazılması, Clean Code + TDD disiplinine uyması istendi.

Mevcut durum: Tek dosyalık `main.py` (137 satır) — FastAPI app, in-memory veri,
basit chat, MiniMax çağrısı hep aynı modülde. Bu yapı:
- Test edilemiyor (her test gerçek MiniMax API key ister).
- İş kuralı yok denecek kadar zayıf, hep string matching.
- Agent kavramı henüz oluşmamış; tool calling yok.

Hackathon kodu "çalışır prototip" istiyor (PDF), ama kullanıcının açık tercihi
**disiplinli, test edilebilir** bir yapı. Bu nedenle pragmatik bir layered
yaklaşım seçildi (hexagonal ekstra boilerplate getirir; düz tek modül TDD'yi
imkansız kılar).

Özel zorluk: **Agent non-deterministic bir orchestrator**. Klasik layered
mantıkta "use case" olarak application service'e tıkmak kavramsal yalan olur;
çünkü agent'ın iç parçaları (conversation loop, tool registry, tool dispatcher,
mesaj geçmişi yönetimi) application servisleriyle aynı kategoride değil.
Bu yüzden agent **ayrı bir katman** olarak konumlanır.

## Decision

### 1. Klasör yapısı

```
src/
  domain/                  # Saf iş kuralları, framework yok
    products/
    orders/
    shipping/
    notifications/

  application/             # Use case'ler, port arayüzleri
    ports/                 # Abstract: Repository, LLMClient, Notifier, Scheduler
    services/              # StockService, OrderService, ShippingService, ...

  agent/                   # Agent katmanı (tek agent, düz yapı)
    tools/
      definitions.py       # LLM'in göreceği JSON schema'lar
      registry.py          # Tool adı → callable haritası
      dispatcher.py        # Tool call'u doğru servise yönlendirir
    conversation.py        # Mesaj geçmişi + sistem prompt
    loop.py                # Çağır → tool çalıştır → tekrar et

  infrastructure/          # Port implementasyonları (dış dünya adapter'ları)
    db/
    llm/
    notifiers/
    scheduler/

  presentation/            # HTTP yüzeyi + composition root
    api/
      routes/
      schemas.py
      dependencies.py
    main.py                # FastAPI app, DI kurulumu

tests/
  unit/
    domain/
    application/
    agent/
  integration/
    db/
    llm/                   # Sınırlı; CI'da skip edilebilir
  e2e/
    api/
```

### 2. Bağımlılık yönü

```
presentation → agent → application → domain
                  ↓         ↓
              infrastructure  (port'ları implement eder)
```

- `domain` hiçbir şeye bağımlı değil.
- `application` yalnızca `domain`'e bağımlı + kendi `ports/` arayüzlerini tanımlar.
- `agent` `application`'ı kullanır; LLM erişimi için `application/ports/llm_client.py`'i çağırır.
- `infrastructure` `application/ports/`'taki arayüzleri implement eder; başka katmanlardan **import edilmez**, sadece composition root'tan instantiate edilir.
- `presentation` composition root'tur: FastAPI Depends ile somut adapter'ları port arayüzlerine bağlar.

### 3. Agent'ın anatomisi (bu mimaride yeri)

Agent yedi mantıksal parçaya ayrılır; her biri net bir dosyaya düşer:

| Parça | Yeri |
|-------|------|
| LLM client (HTTP I/O) | `infrastructure/llm/` (port: `application/ports/llm_client.py`) |
| Tool şemaları | `agent/tools/definitions.py` |
| Tool implementasyonu | `application/services/*` (zaten application işi) |
| Tool dispatcher | `agent/tools/dispatcher.py` |
| Conversation loop | `agent/loop.py` |
| Conversation state | `agent/conversation.py` |
| Policy / guardrails | `agent/loop.py` içinde, gerekirse ayrı modül |

### 4. Test stratejisi

Hedef: **TDD disiplini birinci sınıf vatandaş.** Her katmanın testi, o katmanın
sorumluluğuyla **eşleşir**; test ne bir altındaki ne bir üstündeki katmanın işini
yapar. Bütün testler `tests/` altında, üretim koduyla **simetrik klasör**
yapısında yaşar (`src/domain/products/stock_policy.py` → `tests/unit/domain/products/test_stock_policy.py`).

#### 4.1 Katman bazlı kurallar

| Katman | Test türü | Hız hedefi | İzole edilen | Kullanılan teknik |
|--------|-----------|------------|--------------|-------------------|
| `domain/` | Birim | < 10ms / test | Hiçbir şey (tamamen saf) | Düz pytest, parametrize; mock yasak |
| `application/` | Birim | < 50ms / test | DB, LLM, HTTP, scheduler | **Fake** port implementasyonları (in-memory `FakeRepository`, `FakeNotifier`); `unittest.mock` yalnızca son çare |
| `agent/` | Birim | < 100ms / test | Canlı LLM | **Scripted `FakeLLMClient`** — testin başında "LLM şu tool'u şu parametrelerle çağıracak, sonra şu cevabı verecek" diye programlanır. Application servisleri **gerçek** (fake repo ile). |
| `infrastructure/db/` | Entegrasyon | < 500ms / test | — | Gerçek SQLite (in-memory `:memory:` veya tmp file); her test izole transaction/temiz şema |
| `infrastructure/llm/` | Entegrasyon | — | — | Canlı LLM çağrısı; **default'ta skip**, `--run-live` flag'i ile çalışır; CI'da nightly job |
| `infrastructure/notifiers/`, `scheduler/` | Entegrasyon | < 200ms / test | — | Adapter'ın yan etkisi spy/recorder ile doğrulanır |
| `presentation/` | E2E | < 1s / test | Canlı LLM | FastAPI `TestClient`; DI override ile `LLMClient` fake'lenir; DB gerçek (in-memory SQLite) |

#### 4.2 Coverage hedefi

- **`domain/` ve `application/`**: zorunlu **%90+** satır kapsama, **%85+** branch kapsama.
- **`agent/`**: zorunlu **%85+** satır kapsama (loop'un her dalı + dispatcher'ın tüm tool'ları test edilir).
- **`infrastructure/`**: zorunlu **%70+** satır kapsama (adapter'lar daha çok entegrasyon ile doğrulanır; bazı hata yolları sınırlı test edilir).
- **`presentation/`**: zorunlu **%80+** satır kapsama (kritik akışlar E2E ile zincirleme test edilir).
- **Toplam proje coverage'ı**: **%85+** ve düşmemeli. Coverage `pytest-cov` ile ölçülür; CI bu eşiklerin altında **kırılır**.

#### 4.3 FIRST disiplini (clean-code.md)

Her test:
- **Fast** — birim testler ms cinsinden; tüm birim süiti < 5 saniye.
- **Independent** — test sırası önemsiz; paralel çalışabilir (`pytest-xdist`).
- **Repeatable** — saat, network, rastgelelik yok; gerekirse `freezegun` / sabit seed.
- **Self-Validating** — assertion ile otomatik pass/fail; print + manuel okuma yasak.
- **Timely** — testler üretim kodundan **önce** yazılır (kırmızı → yeşil → refactor).

#### 4.4 Test isimlendirme ve yapısı

- Dosya: `test_<modül>.py`
- Test fonksiyonu: `test_<özne>_<beklenen davranış>_<bağlam>` — örnek: `test_stock_policy_marks_below_threshold_when_quantity_under_min_level`
- Yapı: **Arrange / Act / Assert** üç parça net ayrılır; her test **tek bir davranışı** doğrular (çoklu assert tek davranışı doğruluyorsa serbest).
- Parametrize: aynı kuralın varyasyonları `@pytest.mark.parametrize` ile birleştirilir; tekrar test yasak.

#### 4.5 Fake vs Mock seçimi

- **Fake (tercih edilen)**: `application/ports/` arayüzünü implement eden, in-memory davranan gerçek sınıf — örn. `FakeProductRepository`. Davranışı gerçeğe yakın; kırılgan değil; birden fazla testte yeniden kullanılır.
- **Mock (son çare)**: `unittest.mock` ile yalnızca tek bir etkileşimi doğrulamak gerekiyorsa (örn. "notifier çağrıldı mı?"). Aşırı mock kırılgan test = bakım borcu.
- **Spy/Recorder**: yan etki (notification gönderildi, log atıldı) doğrulanırken kayıt tutan fake adapter.

#### 4.6 Fixture stratejisi

- `tests/conftest.py` — proje geneli fixture'lar (örn. `clock`, `seeded_random`).
- `tests/unit/application/conftest.py` — fake repository fabrika fixture'ları.
- `tests/unit/agent/conftest.py` — `FakeLLMClient` builder; "şu mesaj geldiğinde şu tool'u çağır" script'leme yardımcısı.
- `tests/integration/conftest.py` — `sqlite_engine`, `db_session` fixture'ları (test scope'lu).
- `tests/e2e/conftest.py` — FastAPI `TestClient` + DI override.

#### 4.7 Agent için özel test pattern'leri

Agent testleri **deterministik** olmalı — bu zor kısım. Üç pattern:

1. **Scripted conversation**: `FakeLLMClient` sıralı yanıtlar kuyruğu tutar. Test "kullanıcı X dedi → LLM ilk yanıtı: tool_call(get_stock, 'domates'), ikinci yanıtı: 'Domates stoğu 40 kg' " gibi script'lenir. Loop'un script'i doğru takip ettiği doğrulanır.
2. **Tool invocation assertion**: `FakeLLMClient` hangi tool'un hangi parametreyle çağrıldığını kaydeder; test sonunda `assert client.calls == [...]` ile doğrulanır.
3. **Guardrail testleri**: "Policy şu tool'u engellemeli" senaryoları için ayrı testler — agent'ın iş kuralı kararlarını da doğrular.

#### 4.8 Yasaklar (test tarafı)

- Test içinde `time.sleep` yasak (flaky'liğin ana kaynağı).
- `pytest.mark.skip` gerekçesiz yasak; her skip bir issue/ADR'a bağlanır.
- Canlı LLM API çağrısı birim test süitinde yasak (sadece `infrastructure/llm/` entegrasyon süitinde, ayrı flag ile).
- Test verisi gerçek müşteri/sipariş ID'sine bağlı olamaz; fixture'tan gelir.
- "Test geçsin diye" production kodunda branch açmak yasak (`if is_test: ...` deseni yasak).

Bu stratejinin ödülü: **agent davranışı API key olmadan, deterministik şekilde test edilir** ve refactor güvenli olur — TDD doğal akar.

### 5. Mevcut `main.py`'ın taşınması

Bu ADR Accepted olunca yapılacak refactor (ayrı commit'te):

- `app = FastAPI()` + middleware → `src/presentation/main.py`
- `products`, `orders` listeleri → geçici olarak `infrastructure/db/in_memory_*.py`'ye taşınır (Sprint-0); sonraki ADR'da SQLite'a geçilir.
- `/products`, `/orders` route'ları → `src/presentation/api/routes/products.py`, `orders.py`
- `/chat` (string match) → silinir; yerine agent kullanacak.
- `/ai-chat` MiniMax çağrısı → `infrastructure/llm/minimax_client.py` + `agent/loop.py` parçalarına bölünür.
- `static/` ve `FileResponse("static/index.html")` → `presentation/main.py`'da kalır (frontend kararı ayrı ADR).

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **A) Düz `main.py` + birkaç modül (`services/`, `repositories/`)** | Hızlı yazılır ama agent'ın conversation loop'u nereye gideceği belirsiz; test için her yerde mock gerekir. "Disiplinli, büyük proje gibi" hedefini karşılamaz. |
| **B) Layered ama agent application içinde (3 katman)** | Kavramsal yalan: agent'a özel kavramlar (loop, registry, dispatcher) application'da yabancı. İkinci agent eklemek application'ı kirletir. |
| **C) Hexagonal / Ports & Adapters (full)** | TDD için en saf yapı; ancak her domain için port + adapter ikilisi boilerplate getirir. Hackathon süresinde derinlik kaybı riski. Layered + port yaklaşımı bu faydanın %80'ini, maliyetin %30'una verir. |
| **D) `agent/customer/`, `agent/admin/` gibi çoklu agent için önden organizasyon** | YAGNI ihlali. Tek agent yapacağız; ikinci agent ihtiyacı doğarsa yeniden organize edilir. |
| **E) `app/` prefix'i `src/` yerine** | İkisi de yaygın; `src/` daha standart Python pratiği ve test/import yollarında daha temiz davranır. |

## Consequences

### Olumlu

- Domain ve application **API key, DB, HTTP olmadan** test edilebilir → TDD doğal akar.
- Agent'a özel kavramlar (loop, registry, dispatcher) doğal yerinde; agent kodu okunabilir kalır.
- LLM sağlayıcı değişimi (MiniMax → Claude → OpenAI) **bir adapter** değişimi olur, domain'e dokunmaz.
- DB değişimi (in-memory → SQLite → Postgres) yalnızca `infrastructure/db/` değişimidir.
- İkinci agent (örn. proaktif scheduler-agent) gerektiğinde mimari **patlamaz**; `agent/` altında yeniden organize edilir.
- Sunumda "katmanlı + agent ayrı + port/adapter" hikâyesi jüri için güçlü mimari iddia.

### Olumsuz

- Tek dosyalık `main.py`'a kıyasla dosya/klasör sayısı belirgin artar; küçük değişiklikler için birden fazla dosyaya dokunmak gerekir.
- DI'yi composition root'ta toplama disiplini şart; ihlal edilirse mimari aksamaya başlar — kod review'da bu kuralın gözetilmesi gerekir.
- Hackathon süresinin ilk %20'si refactor ve iskelete gider; yeni feature daha geç başlar. Karşılığında sonraki adımların **hızı artar** (her özellik kendi yerine düşer).
- Test piramidi disiplinini gerektirir: birim testler **fake** ile yazılır, gerçek adapter testleri sınırlı tutulur — aksi halde test süitleri yavaşlar ve CI'da kırılganlık artar.

## Open items

- [ ] `src/` iskeletini oluştur (`mkdir -p src/{domain,application/ports,application/services,agent/tools,infrastructure/{db,llm,notifiers,scheduler},presentation/api/routes} tests/{unit,integration,e2e}`).
- [ ] Mevcut `main.py`'ı bu ADR'daki haritaya göre dağıt (ayrı bir commit, "refactor: main.py'ı layered yapıya taşı").
- [ ] `src/`'i import yolu olarak ayarla (`pyproject.toml` veya `PYTHONPATH`).
- [ ] `pytest` konfigürasyonu (`pytest.ini` veya `pyproject.toml` `[tool.pytest.ini_options]`) + `tests/` keşfi.
- [ ] İlk concept sayfası: `docs/concepts/katman-haritasi.md` — "şu dosya nereye gider?" karar akışı.
- [ ] CI'da `domain/` ve `application/` katmanlarında concrete adapter import yasağını otomatik kontrol et (`import-linter` veya `grimp`). Katman ihlali CI'ı kırar.
- [ ] CI'da coverage eşiği zorunlu (`pytest --cov --cov-fail-under=85`); eşik altı CI kırılır.
- [ ] CI'da `ruff` + `mypy` (strict) çalışır; tip ihlali ve lint hatası CI'ı kırar.

## Affected areas

- `main.py` — bu ADR ile parçalanıp `src/presentation/main.py`'a taşınır
- `static/` — `presentation/` altında kalmaya devam eder
- `requirements.txt` — gelecek ADR'larda (SQLAlchemy, APScheduler, vb.) genişleyecek
- [[0001-hackathon-kapsami-temalar]] — bu mimari, oradaki beş temayı uygulamak için tasarlandı
- _gelecek ADR'lar_ — LLM seçimi, persistans, scheduler, frontend kararları **bu mimarinin somut adapter seçimleri** olarak konumlanır
