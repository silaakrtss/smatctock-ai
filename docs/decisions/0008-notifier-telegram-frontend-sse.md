# ADR 0008: notifier-telegram-frontend-sse

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Bildirim kanalları iki adapter olarak implement edilir:
> **`TelegramNotifier`** (BotFather token + chat_id, `httpx` ile direkt API,
> ek SDK yok) ve **`FrontendNotifier`** (DB'ye `Notification` kaydı + **Server-Sent
> Events (SSE)** ile açık tarayıcılara anlık push). Bir **`FanoutNotifier`** her
> bildirimi **iki kanala paralel** gönderir; her `notify_manager()` ve
> `notify_customer()` çağrısı hem Telegram'a hem frontend'e düşer. Müşteri
> bildirimleri frontend'de sipariş takip ekranında gerçek olarak gösterilir;
> Telegram tarafında manager view'ında özet olarak görünür.
>
> **Kapsam:** `src/application/ports/notifier.py`, `src/infrastructure/notifiers/`
> (Telegram, Frontend, Fanout adapter'ları), `src/presentation/api/routes/notifications.py`
> (SSE endpoint + REST list endpoint), domain `Notification` entity'si ve
> `NotificationLog` repository'si.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **Telegram ve Frontend implementasyon detayları `infrastructure/notifiers/`
>   dışında import edilemez.** Üst katmanlar yalnızca
>   `application/ports/notifier.py`'deki `Notifier` port'unu görür.
> - **Spam engelleme adapter'ın işi değildir.** Adapter saf bir kanal;
>   `NotificationLog` kontrolü ve cooldown kuralı **application
>   service'inde** (`NotificationService`) uygulanır. Adapter mesajı
>   sorgusuz iletir.
> - **Telegram mesaj formatı (MarkdownV2 escape) adapter'ın iç meselesidir.**
>   Domain `Notification` dataclass'ı kanal-bağımsız (kategori, başlık, gövde);
>   format çevrimi adapter sınırında yapılır.
> - **SSE bağlantısı in-memory broadcast hub üzerinden yayılır.** Hub
>   `infrastructure/notifiers/sse_hub.py`'de yaşar; presentation katmanı
>   yalnızca port'u görür, hub'ı bilmez.
> - **Fanout adapter, alt adapter'lardan biri başarısız olsa diğerine
>   göndermeye devam eder.** Bir kanalın hatası diğerini bloklamaz; hata
>   loglanır, üst katmana sızmaz (best-effort delivery).
> - **`MANAGER_CHAT_ID` env değişkeni eksikse Telegram adapter devre dışı
>   kalır** (uyarı log'lar) ama uygulama başlar; FrontendNotifier tek
>   başına çalışır. CI ve dev ortamı bu sayede Telegram token'ı olmadan
>   çalışır.
> - **SSE endpoint'inde authentication şu sürümde yok**; hackathon ölçeği için
>   kabul edilir. Production gerekirse ayrı ADR.

## Context

ADR-0007 üç scheduler job'u (`check_stock_thresholds`, `check_shipping_delays`,
`morning_briefing`) ve agent tool'ları "yöneticiye bildir", "müşteriye bildir"
çağıracak. ADR-0002 `application/ports/notifier.py` port'unu yer olarak
ayırdı ama somut kanal yok.

Mevcut durum:
- Hiçbir bildirim altyapısı yok; PDF "kargo gecikme tespit edildi → müşteriyi
  ve yöneticiyi bilgilendir" örneklerini sözde bırakıyoruz.
- Frontend kararı (ADR-0001 Open item, ileride ADR-0009 olarak konumlandı)
  ertelendi; ancak demo'da "proaktif aksiyon" iddiasının görsel kanıtı
  olmadan jüri etkisi zayıf.

Kısıtlar:
1. **Hızlı kurulum** — kredi kartı isteyen ya da onay süreci uzun
   (WhatsApp Business, Twilio prod) kanallar imkansız.
2. **Hedef kitle uyumu** — PDF "WhatsApp/mesajlaşma uygulaması" örneği
   veriyor. Telegram aynı kategoride; jüriye "WhatsApp Business onayı
   haftalar, Telegram aynı prensibin uygulanabilir kanıtı" denilebilir.
3. **Demo görseli** — scheduler tetiklendiğinde bildirimin **gözle görünür**
   olması iddianın kanıtıdır. Telegram mobil push + tarayıcıda anında
   beliren panel ikisi birden güçlü hikâye.
4. **Müşteri tarafı** — gerçek müşteri Telegram chat_id'leri yok; ama
   müşteri bildirim akışı **frontend sipariş takip ekranında** gerçek
   olarak gösterilebilir.
5. **Test/CI** — bildirim adapter'ı API key olmadan çalışmalı; aksi halde
   CI kırılır veya geliştirme yavaşlar.

## Decision

### 1. İki kanal, paralel fanout

İki concrete adapter:

- **`TelegramNotifier`** — manager bildirimleri için anlık push. BotFather'dan
  alınan token + `MANAGER_CHAT_ID` ile çalışır.
- **`FrontendNotifier`** — DB'ye `Notification` kaydı yazar + in-memory SSE
  broadcast hub'ı üzerinden açık tarayıcılara push eder.

Bir **`FanoutNotifier`** her ikisini birden çağırır; üst katman tek bir
`Notifier` port'u görür. Telegram veya Frontend adapter'ı tek başına
kullanmak mümkün (composition root'ta seçim), ama default Fanout'tur.

### 2. Telegram adapter

- Implementasyon: **`httpx` ile direkt Telegram Bot API** (`sendMessage`
  endpoint'i). Resmi `python-telegram-bot` SDK eklenmiyor; tek endpoint
  kullanıyoruz, SDK'nın getirdiği büyük bağımlılık ağacı gereksiz.
- Mesaj formatı: **MarkdownV2**; kategoriye göre emoji prefix'i:
  - `stock_alert` → 🔴 (kritik stok)
  - `delay_alert` → ⚠️ (kargo gecikmesi)
  - `morning_briefing` → ☀️ (sabah özeti)
  - `order_status` → 📦
- Müşteri bildirimleri Telegram'da manager view'ına "📨 Müşteri Ali'ye
  bildirildi: ..." formatında **özet** olarak gönderilir; gerçek müşteri
  Telegram chat'i yok.
- Hata yönetimi: Telegram API hatası → 3 deneme + exponential backoff
  (250ms, 750ms, 2s) → sonra `NotifierError`. Fanout adapter bu hatayı
  loglar, frontend kanalı bloklanmaz.
- `MANAGER_CHAT_ID` veya `TELEGRAM_BOT_TOKEN` eksikse adapter
  **noop davranır** ve uygulama başlangıcında bir uyarı log'lar. Bu, CI
  ve dev ortamının token'sız çalışmasını sağlar.

### 3. Frontend adapter (DB + SSE)

İki sorumluluğu vardır:

1. **DB'ye yaz** — `NotificationLog` repository'sini (ADR-0006'da öngörülen)
   kullanarak `Notification` kaydı oluşturur. Bu sayede sayfa yenilendiğinde
   geçmiş bildirimler görünür; SSE bağlantısı henüz açılmadığında bile
   bildirim kaybolmaz.
2. **SSE hub'ına yayınla** — `infrastructure/notifiers/sse_hub.py` in-memory
   pub-sub. Hub, açık tarayıcı bağlantılarını (asyncio queue listesi) tutar;
   `publish(notification)` her queue'ya event yazar.

### 4. SSE hub mimarisi

- Yer: `src/infrastructure/notifiers/sse_hub.py`.
- API:
  ```python
  class SseHub:
      async def subscribe(self) -> AsyncIterator[NotificationEvent]: ...
      async def publish(self, event: NotificationEvent) -> None: ...
  ```
- Yapı: dict[`subscriber_id`, `asyncio.Queue`]. Her HTTP SSE bağlantısı
  yeni bir queue açar, bağlantı kopunca queue silinir.
- Lifespan: tek bir hub instance, FastAPI lifespan'da yaratılır,
  composition root'ta DI ile bağlanır.
- Single-process kısıtı: Çoklu uvicorn worker'da hub paylaşılmaz; hackathon
  ölçeğinde tek worker kabul edilir. Production gerekirse Redis pub-sub'a
  geçiş ayrı ADR.

### 5. SSE endpoint'i (presentation)

- Route: `GET /notifications/stream` → `StreamingResponse` (`text/event-stream`).
- Akış:
  ```python
  @router.get("/notifications/stream")
  async def stream(hub: SseHub = Depends(get_hub)):
      async def event_generator():
          async for event in hub.subscribe():
              yield f"data: {event.to_json()}\n\n"
      return StreamingResponse(event_generator(), media_type="text/event-stream")
  ```
- Frontend tarayıcı tarafı standart `EventSource` API kullanır.
- Geçmiş bildirimleri çekmek için **ayrı REST endpoint**:
  `GET /notifications?limit=50&category=...` — sayfa yüklendiğinde son N
  bildirim listelenir.
- Authentication şu sürümde yok; hackathon kapsamında kabul edilir.

### 6. Port arayüzü

`src/application/ports/notifier.py`:

```python
from abc import ABC, abstractmethod
from src.domain.notifications.notification import Notification


class Notifier(ABC):
    @abstractmethod
    async def send(self, notification: Notification) -> None: ...


class NotifierError(Exception):
    """Adapter'a özel hata; üst katman best-effort kabul eder."""
```

Domain `Notification` dataclass'ı:

```python
@dataclass(frozen=True)
class Notification:
    recipient: Recipient   # ManagerRecipient | CustomerRecipient (sealed)
    category: NotificationCategory  # Enum
    title: str
    body: str             # Plain text; format çevrimi adapter'da
    metadata: dict[str, str] = field(default_factory=dict)  # adapter'a hint
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
```

`Recipient` sealed dataclass hiyerarşisi: `ManagerRecipient()` ve
`CustomerRecipient(order_id, customer_name)`. Adapter recipient tipine göre
yönlendirme yapar (Frontend: ikisini de DB'ye yazar, SSE topic ayrımı;
Telegram: manager için chat_id'ye, customer için manager chat'ine özet).

### 7. Spam engelleme yeri

Adapter saf kanal; **`NotificationService`** (application katmanı) çağrı
öncesi `NotificationLog`'a bakar:

- Aynı `(category, recipient, related_entity_id)` üçlüsü için **6 saatlik
  cooldown** (eşik uyarıları için kritik; aynı domates'in stok düşüklüğü
  saatte bir bildirilmez).
- `morning_briefing` günde bir tetiklendiği için cooldown'a tabi değil.
- Cooldown ihlali → service bildirim göndermeden çıkar, debug log'lar.

### 8. Fanout adapter davranışı

`FanoutNotifier(Notifier)` iç listesi: `[TelegramNotifier, FrontendNotifier]`.

```python
async def send(self, notification: Notification) -> None:
    results = await asyncio.gather(
        *(adapter.send(notification) for adapter in self._adapters),
        return_exceptions=True,
    )
    for adapter, result in zip(self._adapters, results, strict=True):
        if isinstance(result, Exception):
            logger.exception("Adapter %s failed", adapter.__class__.__name__, exc_info=result)
```

- Her adapter paralel çalışır; biri başarısız diğerini etkilemez.
- Tüm adapter'lar başarısız olsa bile `send()` exception fırlatmaz —
  best-effort delivery. Hata akışı log'lar üzerinden izlenir.

### 9. Test stratejisi

- **Adapter birim testi (Telegram)**: `httpx.MockTransport` ile API çağrısı
  simüle edilir; MarkdownV2 escape doğrulanır; retry davranışı test edilir.
- **Adapter birim testi (Frontend)**: fake `NotificationLogRepository` +
  fake `SseHub` ile DB yazımı ve hub publish doğrulanır.
- **SseHub birim testi**: çoklu subscriber'a publish, subscribe iptali
  (cancel) ve queue temizliği test edilir.
- **Fanout birim testi**: bir adapter exception fırlattığında diğerinin
  hâlâ çağrıldığı doğrulanır.
- **E2E SSE testi** (`tests/e2e/api/`): `TestClient` ile `/notifications/stream`
  açılır, ayrı bir HTTP çağrısı bildirim üretir, SSE stream'inde event
  görünür.
- **`NotificationService` cooldown testi**: aynı kategori + recipient için
  iki ardışık çağrıda ikincinin atlandığı doğrulanır.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **WhatsApp Business API** | Meta onay süreci haftalar; hackathon zaman çizelgesine sığmaz. |
| **Twilio WhatsApp sandbox** | Hesap açma + sandbox join akışı demo'yu kirletir; jüriye "telefondan join et" demek pratik değil. |
| **SMTP / e-posta** | Demo'da görsel etkisi düşük (mail kutusu açmak kimseye heyecan vermez); spam filter, gecikme. Ek kanal olarak değer marjinal. |
| **Discord/Slack webhook** | Telegram'a kıyasla ek değer yok; tek kanal seçilirse Telegram daha "müşteriye yakın" kategori. |
| **`python-telegram-bot` SDK** | Tek endpoint (`sendMessage`) kullanıyoruz; SDK'nın update polling, conversation handler gibi büyük altyapısı bizim için gereksiz bağımlılık. `httpx` zaten yığında var (ADR-0003), direkt API daha sade. |
| **WebSocket (frontend için)** | SSE bizim akışta (sunucudan istemciye tek yönlü) yeterli; WebSocket çift yönlü, daha karmaşık; SSE'nin native `EventSource` API'si tarayıcıda daha az kod. |
| **Polling (frontend her 5sn `/notifications`)** | Trafik yüksek, gerçek-zamanlı hissi yok, batarya/CPU yiyici. SSE aynı işin daha temiz versiyonu. |
| **Yalnızca DB + sayfa refresh** | "Anlık" iddiasını öldürür; scheduler tetiklediğinde paneli refresh etmek gerekir, demo akıcılığı düşer. |
| **Kategori bazlı kanal ayrımı (stock_alert→Telegram, briefing→frontend)** | Her bildirim **iki yere de** gitsin daha basit ve güçlü. Manager hem mobilde hem dashboard'da görür; redundant ama best-effort. |
| **`notify_customer` simüle (frontend yok, sadece log + manager chat'inde özet)** | Önerilmişti; ancak frontend zaten gelecek, müşteri bildirimini gerçek bir UI'da göstermek Tema 1+3 iddiasını **gerçek** yapar. Hackathon değerini artırır. |
| **SSE hub'ı için Redis pub-sub** | Production-grade; ama Redis kurulum yükü. Tek worker varsayımıyla in-memory hub yeterli; gerekirse ayrı ADR. |
| **`tenacity` ile retry** | Üç deneme + backoff için bağımlılık eklemek gereksiz; 10 satırlık manuel retry yeterli. |
| **Bildirim authentication'ı (JWT/session)** | Hackathon kapsamı ve demo akıcılığı için kapsam dışı; jüri "neden auth yok?" derse "tek worker, tek demo kullanıcısı, kapsam dışı" cevabı verilir. |

## Consequences

### Olumlu

- **Demo görseli güçlü**: Manager Telegram'da push alır + dashboard'da
  panel anında parlar. Tema 3, 4, 5 iddialarının görsel kanıtı kuvvetli.
- **Tema 1 müşteri etkileşimi gerçekleşir**: Müşteri sipariş takip
  ekranında bildirimleri görür; "agent müşteriye bildirdi" iddiasının
  gerçek UI kanıtı var.
- **Best-effort delivery** (fanout + paralel) bir kanalın çökmesi diğerini
  bloklamıyor; uygulama tek bir adapter'a bağımlı değil.
- **CI/dev token'sız çalışır**: Telegram noop fallback'i sayesinde test ve
  geliştirme akışları engelsiz.
- **SSE'nin ek bağımlılığı sıfır**: FastAPI native `StreamingResponse` +
  tarayıcı native `EventSource`. Yığına yeni paket girmiyor.
- **Mimari iddia güçlü**: "Bir port, iki adapter, fanout pattern"
  port/adapter disiplininin somut göstergesi.

### Olumsuz

- **SSE hub in-memory** → çoklu uvicorn worker (gunicorn `--workers 4`)
  bildirimleri paylaşmaz. Hackathon tek worker sınırı kabul edilir;
  jüri sorarsa "Redis pub-sub'a geçiş bir adapter değişimi" cevabı verilir.
- **MarkdownV2 escape detayı** Telegram tarafında bakım borcu; özel
  karakterler (`*`, `_`, `\`) escape edilmezse mesaj kırılır. Adapter
  testleri bu edge case'leri kapsamak zorunda.
- **Müşteri bildirim modelinde kimlik doğrulama yok**; herhangi bir
  tarayıcı `/notifications/stream`'i dinler. Hackathon kapsamında kabul;
  production'da auth gerekir.
- **`NotificationLog` cooldown kuralı** application service'inde; bu
  kuralın test edilmesi gerekiyor, aksi halde demo'da Telegram aynı
  uyarıyı her saat başı yağdırabilir.
- **Fanout best-effort** yan etkisi: bir kanaldaki kalıcı arıza sessizce
  log'a düşer. Production gözlem (Prometheus/sentry) gerekir; hackathon
  için log yeterli.

## Open items

- [x] `pyproject.toml`: ek bağımlılık yok. *(httpx zaten yığında, F1.2)*
- [x] `application/ports/notifier.py` — `Notifier` port + `NotifierError`. *(F3.2)*
- [x] `domain/notifications/notification.py` — Notification dataclass + Channel/Status enum. *(F2.5; sealed Recipient hiyerarşisi yerine düz string recipient tercih edildi — `Recipient` polymorphism YAGNI olduğu için tek string alan)*
- [x] `telegram_notifier.py` — httpx + MarkdownV2 escape + retry. *(F7.5 — kategori emoji prefix'i: 🔴 stok, ⚠️ kargo, ☀️ brifing, 📦 sipariş; token yoksa noop)*
- [x] `sse_hub.py` — in-memory pub-sub. *(F7.6 — AsyncQueue tabanlı; F10.2 fix'iyle disconnect/cancel temizliği eklendi)*
- [x] `frontend_notifier.py` — DB + hub publish. *(F7.6)*
- [x] `fanout_notifier.py` — paralel send, best-effort. *(F7.7 — asyncio.gather + per-notifier exception izolasyonu)*
- [x] `notification_service.py` — adapter'a delegasyon. *(F3.6 dispatch + F6.1 `notify_customer` helper)*
- [x] `routes/notifications.py` — REST list + SSE stream. *(F8.4; F10.2 fix'iyle SSE bağlantı yaşam döngüsü iyileştirildi)*
- [x] Settings: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. *(F1.6, F5.1; `notifier_channel: Literal[...]` kullanılmadı — composition root sabit FanoutNotifier kuruyor, runtime seçim ihtiyacı doğmadı)*
- [x] `.env.example` güncellemesi. *(F1.6 + F8 boyunca senkron tutuldu)*
- [x] Frontend bildirim paneli. *(F8.6 dashboard.html — `/notifications` initial fetch + `/notifications/stream` EventSource + Alpine x-data; F10.1-10.2'de visibility-aware lifecycle eklendi)*
- [x] Adapter birim testleri. *(F7.5-F7.7 — Telegram 6, SseHub 3, Frontend 1, Fanout 3 = 13 birim test)*
- [ ] **`NotificationLog` repository + cooldown spam engelleme.** *(Ayrı `notification_log` tablosu yazılmadı; mevcut `notifications` tablosu zaten her dispatch'i kaydediyor. Ancak `NotificationService`'te cooldown kuralı **henüz yok** — aynı bildirim her job tetiklemesinde yeniden gönderilir. Hackathon ölçeği için kabul edilebilir; production'da kritik açık iş.)*
- [ ] E2E SSE testi (`test_notifications_stream.py`). *(StreamingResponse'u TestClient ile test etmek pratikte zor; F8.4'te dolaylı testler ve canlı smoke yapıldı. Async iterator'ı doğrulayan formal E2E test eklenmedi.)*
- [ ] `NotificationService` cooldown birim testi. *(Cooldown kuralı yok — yukarıdaki açık ile birlikte gelir.)*

## Affected areas

- `src/application/ports/notifier.py`, `notification_log_repository.py` —
  port arayüzleri.
- `src/domain/notifications/` — `Notification`, `Recipient`, `NotificationCategory`.
- `src/application/services/notification_service.py` — cooldown + log + send.
- `src/infrastructure/notifiers/` — Telegram, Frontend, SseHub, Fanout adapter'ları.
- `src/infrastructure/db/` — `notification_log` tablosu ve repository
  implementasyonu (ADR-0006 şemasına eklenir).
- `src/presentation/api/routes/notifications.py` — REST + SSE endpoint'leri.
- `src/presentation/main.py` — composition root: FanoutNotifier bağlama,
  SseHub lifespan, Settings.
- `static/index.html` (geçici frontend) — minimal bildirim paneli, EventSource
  dinleyici.
- [[0001-hackathon-kapsami-temalar]] — bu ADR Tema 1, 3, 4, 5'in proaktif
  bildirim iddiasının somut implementasyonudur.
- [[0002-mimari-yaklasim-layered-agent]] — bu ADR oradaki
  `infrastructure/notifiers/` katmanının somut karşılığıdır.
- [[0006-persistans-sqlite-sqlalchemy-imperative-mapping]] —
  `notification_log` tablosu oradaki şema disiplinine uyar.
- [[0007-scheduler-apscheduler-async.md]] — scheduler job'ları bu
  notifier üzerinden çıktı verecek.
- _gelecek ADR_ — Frontend (askıda) bu SSE/REST endpoint'lerini tüketen
  UI katmanını şekillendirecek.
