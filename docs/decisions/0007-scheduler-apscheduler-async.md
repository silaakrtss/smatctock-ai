# ADR 0007: scheduler-apscheduler-async

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Zamanlanmış görevler için **APScheduler 4 (async)** kullanılır;
> FastAPI lifespan'a bağlı **in-process** çalışır. Üç job tanımlanır:
> `check_stock_thresholds` (saat başı, deterministik), `check_shipping_delays`
> (saat başı, deterministik) ve `morning_briefing` (her gün 08:00, LLM destekli
> agent workflow). Job mimarisi **hibrittir**: deterministik job'lar
> doğrudan application service'lerini çağırır; sabah özeti agent workflow'u
> üzerinden geçer. APScheduler **minimal port arayüzü** (`Scheduler`) arkasına
> alınır.
>
> **Kapsam:** `src/infrastructure/scheduler/`, `src/application/ports/scheduler.py`,
> `src/agent/workflows/morning_briefing.py` (LLM'li job için). Tema 4
> (stok eşiği), Tema 3 (kargo gecikme) ve Tema 5 (sabah özet) bu ADR'ın
> somut karşılığıdır.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **APScheduler API'si `infrastructure/scheduler/` dışında import edilemez.**
>   Üst katmanlar yalnızca `application/ports/scheduler.py`'deki `Scheduler`
>   port'unu görür.
> - **Job fonksiyonları saf coroutine'dir.** Scheduler'a bağımlı kalmazlar;
>   doğrudan çağrılabilir ve test edilebilirler. Job içinde `apscheduler.*`
>   import yasak.
> - **Her job kendi `AsyncSession`'ını açar ve kapatır.** Job'lar arası
>   session paylaşımı yasak; transaction sınırı her tetiklemede izole.
> - **Çakışma engellenir.** Her job için `max_instances=1`; süresi geçen
>   tetiklemeler kuyruğa alınmaz, atlanır (`coalesce=True`).
> - **Hata yönetimi: log + devam.** Job hatası loglanır; otomatik retry yok;
>   sonraki tetikleme normal akar.
> - **LLM çağıran job (sabah özeti) `agent/workflows/` altında yaşar**;
>   scheduler yalnızca tetikleyicidir, LLM tool calling mantığı oraya gizlenir.
> - **Cron ifadeleri kod içinde sabit değildir.** Tetikleme zamanları
>   `Settings` üzerinden okunur (varsayılan değerlerle); deploy/dev farkı
>   env ile yönetilir.

## Context

ADR-0001 beş tema iddiası, ADR-0002 layered + agent mimarisi, ADR-0006 SQLite
async DB kararlarından sonra **proaktif tetikleyici** ihtiyacı netleşti:

- **Tema 4 (Stok)** — eşik altı ürünleri otomatik tespit etmek; saatte bir
  DB sorgusu + bildirim + tedarikçi taslağı.
- **Tema 3 (Kargo)** — kargo durumlarını periyodik kontrol, gecikme
  tespitinde müşteri/yönetici bildirimi.
- **Tema 5 (İş Akışı)** — sabah 08:00'de günün siparişlerinin LLM destekli
  özetini üretip yöneticiye iletmek. ADR-0001 TL;DR'ı bu işin "Tema 5
  iddiasının kalbi" olduğunu söylüyor.

Mevcut durumda hiçbir zamanlama altyapısı yok; `main.py` salt request-response.
Manuel tetikleyici (örn. `/cron/check-stock` endpoint'i) demo'da insan
müdahalesi gerektirir; "proaktif aksiyon" iddiasını zayıflatır.

Kısıtlar:
1. Hackathon ölçeği — Redis/Celery gibi broker'lı çözümler ek kurulum yükü.
2. ADR-0002 katman disiplini — scheduler'ın port arkasında yaşaması beklenir.
3. ADR-0006 async pipeline — scheduler async olmalı; sync bridge yasak.
4. Test edilebilirlik — job fonksiyonları scheduler'dan bağımsız test
   edilebilmeli.

## Decision

### 1. Kütüphane: APScheduler 4 (async)

- Paket: `apscheduler>=4.0` (async-native sürüm).
- `AsyncScheduler` doğrudan kullanılır; sync `BackgroundScheduler` yasak.
- FastAPI lifespan'a bağlı (`@asynccontextmanager`); `app` başlatıldığında
  `scheduler.start()`, kapatılırken `scheduler.stop()`.
- Job persistence: in-memory (default). Hackathon ölçeğinde restart toleransı
  gereksiz; gerekirse ileride SQLAlchemy job store eklenir (ayrı ADR).

### 2. Port: `application/ports/scheduler.py`

Minimal arayüz:

```python
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class CronTrigger:
    hour: str = "*"
    minute: str = "0"
    day_of_week: str = "*"


class Scheduler(ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    def add_job(
        self,
        func: Callable[[], Awaitable[None]],
        trigger: CronTrigger,
        *,
        job_id: str,
    ) -> None: ...
```

`Scheduler` port'u APScheduler'ın `BaseTrigger`, `Job`, `Scheduler` tiplerini
ifşa etmez; somut adapter (`infrastructure/scheduler/apscheduler_adapter.py`)
`CronTrigger` dataclass'ını APScheduler `CronTrigger`'ına çevirir.

### 3. Job'lar

#### 3.1 `check_stock_thresholds` (saat başı — deterministik)

- Yer: `src/infrastructure/scheduler/jobs/check_stock_thresholds.py`.
- Tetikleme: `CronTrigger(minute="0")` (her saat başı). `Settings` override
  edebilir.
- Akış:
  1. Yeni `AsyncSession` aç.
  2. `StockService.find_below_threshold()` çağır (application service).
  3. Her eşik altı ürün için `NotificationService.notify_manager(...)` ve
     `SupplierDraftService.create_reorder_draft(...)` çağır.
  4. `last_alerted_at` güncelle (spam'i önlemek için: aynı ürün için 6 saat
     içinde tekrar bildirim yok — kural application service'inde).
  5. Session commit + kapat.
- LLM çağrısı **yok**; saf iş kuralı.

#### 3.2 `check_shipping_delays` (saat başı — deterministik)

- Yer: `src/infrastructure/scheduler/jobs/check_shipping_delays.py`.
- Tetikleme: `CronTrigger(minute="15")` (saat başı çakışmayı kaçırmak için
  15 dakika offset).
- Akış:
  1. Yeni session.
  2. `ShippingService.find_delayed_shipments()` (application service);
     "gecikmiş" tanımı domain `DelayPolicy`'de.
  3. Her gecikmiş kargo için `NotificationService.notify_customer(...)` ve
     `NotificationService.notify_manager(...)`.
  4. Aynı kargo için tekrarlanan bildirim engellenir (`NotificationLog`
     tablosu).
  5. Session commit + kapat.
- LLM çağrısı yok.

#### 3.3 `morning_briefing` (her gün 08:00 — LLM destekli agent workflow)

- Yer: **`src/agent/workflows/morning_briefing.py`** (scheduler yalnızca
  tetikleyici; iş `agent/`'da).
- Tetikleme: `CronTrigger(hour="8", minute="0")`. `Settings` ile override
  edilebilir (dev'de gün içi test için).
- Akış:
  1. Yeni session.
  2. `OrderService.list_today_pending()`, `OrderService.list_today_delivered()`,
     `StockService.list_critical()`, `ShippingService.list_today_dispatched()`
     gibi structured veri toplanır (deterministik kısım).
  3. Bu veri **prompt'a sıkıştırılmış halde** LLM'e (port arkasındaki
     `LLMClient`) verilir; sistem promptu "Türkçe, kısa, yöneticiye yönelik
     günlük özet üret" der.
  4. LLM tool çağırırsa (örn. detay sorgusu için), dispatcher devreye girer.
  5. Üretilen özet `NotificationService.notify_manager(...)` ile gönderilir;
     `NotificationLog` kaydı atılır.
  6. Session commit + kapat.
- Bu job, ADR-0004'ün "kendi agent loop'umuz" kararının **proaktif workflow**
  varyantıdır; reaktif chat agent'ı ile aynı `agent/loop.py` mantığını
  kullanabilir veya basit tek-tur LLM çağrısı yapabilir (implementasyon
  detayı, ADR konusu değil).

### 4. Job kayıt yeri

- `src/infrastructure/scheduler/registry.py` → `register_jobs(scheduler:
  Scheduler, deps: AppDependencies) -> None`.
- Composition root (`src/presentation/main.py`) lifespan'da çağırır:
  ```python
  async with lifespan(app):
      await scheduler.start()
      register_jobs(scheduler, deps)
      yield
      await scheduler.stop()
  ```

### 5. Çakışma ve hata yönetimi

- Her job: `max_instances=1`, `coalesce=True`. Yani:
  - Bir tetikleme önceki çalışmayı geçmişse atlanır (kuyruk birikmez).
  - Aynı job iki kez paralel çalışmaz (SQLite tek yazıcı kısıtıyla uyumlu).
- Hata yakalama: her job kendi içinde `try/except Exception` → `logger.exception(...)`
  → sessizce çık. Otomatik retry yok.
- İstisna: `LLMRateLimitError` (ADR-0005) yakalanıp uyarı log'lanır;
  bir sonraki tetiklemeye bırakılır.

### 6. Ayarlanabilirlik

`Settings` (`pydantic-settings`) içinde:

```python
class SchedulerSettings(BaseSettings):
    stock_check_cron: str = "0 * * * *"      # saat başı
    shipping_check_cron: str = "15 * * * *"  # saat başı + 15dk
    morning_briefing_cron: str = "0 8 * * *" # her gün 08:00
    scheduler_enabled: bool = True           # test/CI'da kapatılabilir
```

Test ortamında `scheduler_enabled=False`; e2e testlerinde job'ları
tetiklemek isteyen senaryo job fonksiyonunu **doğrudan** çağırır
(scheduler bypass).

### 7. Test stratejisi

- **Job birim testleri** (`tests/unit/scheduler/jobs/`): job fonksiyonunu
  saf coroutine olarak doğrudan çağır; fake repository + fake notifier
  + (LLM'li job için) `FakeLLMClient` ile davranış doğrulanır.
- **Adapter testi**: `ApschedulerAdapter`'ın port sözleşmesini doğru
  uyguladığını doğrulayan tek smoke test (`add_job` → trigger çevrimi).
- **Scheduler entegrasyon testi**: tek bir `IntervalTrigger` ile dummy job
  10 saniyede tetiklendiğini doğrula; CI'da skip default, manuel `--run-live`.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **Celery + Redis** | Production-grade ama Redis kurulumu hackathon yükü. Tek süreçte yeterli yetenek var. |
| **arq (Redis)** | Aynı Redis bağımlılığı; ek motivasyon yok. |
| **`asyncio.create_task` + manuel cron parsing** | Boilerplate yüksek (cron parse, drift, çakışma kontrolü). APScheduler bunu hazır veriyor. |
| **Saf `while True: await asyncio.sleep(3600)` loop** | Cron ifadesi yok, dev/prod farkı zor, restart sonrası faz kayar. Ucuz görünür ama bakım borcu yüksek. |
| **Ayrı worker process (subprocess / docker)** | Production-grade ama hackathon için fazla; iletişim/health-check yükü. |
| **Hepsi deterministik (LLM'li job yok)** | Sabah özetini deterministik metin şablonu ile üretmek mümkün ama Tema 5'in "AI destekli özet" iddiasını zayıflatır. |
| **Hepsi agent workflow (eşik kontrolü de LLM ile)** | Eşik kontrolü saf iş kuralı; LLM eklemek hem maliyet hem belirsizlik. "LLM her şeyi yapar" anti-pattern'i. |
| **Port arayüzü olmadan APScheduler doğrudan** | YAGNI argümanı geçerli; ancak ADR-0002 disiplini için minimal port maliyeti küçük, taşınabilirlik kazanımı simgesel de olsa anlamlı. |
| **Tetikleme zamanlarını hard-code etmek** | Test/dev/prod farkı yönetilemez; `Settings` üzerinden okumak küçük maliyet. |
| **Otomatik retry (3 deneme, backoff)** | Hata profili belirsizken retry sessiz bozulmaları gizleyebilir. Log + bekle daha şeffaf; gerçek ihtiyaç doğarsa eklenir. |
| **Üçüncü job'u (`check_shipping_delays`) ertelemek** | Tema 3 iddiasını boşa düşürür; pattern aynı, ek maliyet sıfıra yakın. |

## Consequences

### Olumlu

- Tema 3, 4, 5'in "proaktif aksiyon" iddiası demo'da **gerçek** çalışır:
  scheduler arka planda tetiklenir, müdahale gerekmez.
- Tek süreç → tek deployment, tek log akışı; demo kurulumu basit.
- Port arayüzü sayesinde gelecekte arq/Celery'e geçiş yalnızca adapter
  değişimi olur.
- LLM'li job (`morning_briefing`) ile deterministik job ayrımı net;
  "AI sadece doğru yerde" hikâyesi sunumda güçlü mimari iddia.
- Job fonksiyonları saf coroutine olduğu için **tam test edilebilir**;
  scheduler'ın varlığı testlerde kapatılır.

### Olumsuz

- In-process scheduler: FastAPI restart olursa kaçırılan tetiklemeler
  geri gelmez. Hackathon ölçeğinde sorun değil; ileride `SQLAlchemyJobStore`
  ile persistent job state eklenebilir (ayrı ADR).
- SQLite tek yazıcı + birden fazla saatlik job aynı anda çalıştığında
  kuyruk birikebilir. `max_instances=1` + cron offset (15dk) ile pratikte
  çakışma minimum.
- APScheduler 4 görece yeni; v3'e kıyasla API farkları var. Topluluk
  örneklerinin çoğu hâlâ v3 için yazılmış — ufak öğrenme sürtünmesi.
- `morning_briefing` LLM çağırdığı için rate limit veya API kesintisinde
  o günkü tetikleme atlanır. Karşılığında: deterministik fallback özet
  ihtiyacı doğarsa ayrı bir ADR / Open item olur.

## Open items

- [x] `pyproject.toml` bağımlılığı: `apscheduler>=4.0.0a5`. *(F1.2)*
- [x] `application/ports/scheduler.py` — `Scheduler` port + `CronTrigger` dataclass. *(F3.2; F7.1'de `add_job` async'e taşındı — APScheduler 4 alpha API uyumu)*
- [x] `infrastructure/scheduler/apscheduler_adapter.py` — port impl. *(F7.1 — `start_in_background`, `ConflictPolicy.replace`)*
- [x] `check_stock_thresholds` job. *(F7.2 — saf coroutine, apscheduler import etmiyor; `StockThresholdJobContext` parameter object)*
- [x] `check_shipping_delays` job. *(F7.3 — `ShippingDelayJobContext`, `now` injection ile FIRST: Repeatable)*
- [x] `agent/workflows/morning_briefing.py` — LLM'li sabah özeti workflow. *(F7.4 — AgentLoop + PromptLoader + NotificationService orkestrasyonu; tetikleyici `infrastructure/scheduler/jobs/morning_briefing_job.py`)*
- [x] Lifespan'a scheduler start/stop entegrasyonu. *(F8.7 — `SCHEDULER_ENABLED=true` ise `register_scheduler_jobs` çağrılır; composition root cron expression'larını CronTrigger'a parse eder)*
- [x] Scheduler Settings. *(F8 — `scheduler_enabled`, `scheduler_stock_check_cron`, `scheduler_shipping_check_cron`, `scheduler_morning_briefing_cron`)*
- [x] Job birim testleri. *(F7.2-F7.3 — `tests/unit/infrastructure/scheduler/` 8 test)*
- [x] Demo senaryosunda scheduler kanıtı. *(`docs/concepts/demo-akisi.md` § 4 — "Proaktif tetikleyici"; demo'da scheduler kapalı tutmak tercih edildi, chat'ten tetikleme daha okunabilir)*
- [ ] `infrastructure/scheduler/registry.py` — `register_jobs(...)` ayrı modül. *(`composition.register_scheduler_jobs` fonksiyonu bu rolü doldurdu; ayrı registry.py modülü oluşturulmadı — composition root'ta kalması mimari olarak doğal)*
- [ ] Domain: `DelayPolicy` + spam engelleme `NotificationLog`. *(Shipment.is_delayed(now) basit "expected geçti + delivered yok" mantığıyla ADR-0007'nin orijinal DelayPolicy'sini yerine getiriyor. Cooldown / spam engelleme **henüz yok** — ADR-0008'de notu duruyor, NotificationService'e cooldown eklemek gerekirse açık iş)*
- [ ] `morning_briefing` job için cron tetikleyici composition'a bağlama. *(Workflow F7.4'te var ama scheduler'a otomatik kayıt edilmedi — F8.7 yalnızca stock+shipping bağlıyor. Manuel `register_morning_briefing` bağlanması gerekirse açık iş)*

## Affected areas

- `src/application/ports/scheduler.py` — port arayüzü.
- `src/infrastructure/scheduler/` — adapter + jobs + registry.
- `src/agent/workflows/morning_briefing.py` — LLM'li job.
- `src/presentation/main.py` — lifespan entegrasyonu.
- `src/presentation/config/settings.py` — `SchedulerSettings`.
- `pyproject.toml` — `apscheduler>=4.0` bağımlılığı.
- [[0001-hackathon-kapsami-temalar]] — bu ADR Tema 3, 4, 5'in proaktif
  iddialarının somut tetikleyicisidir.
- [[0002-mimari-yaklasim-layered-agent]] — bu ADR oradaki
  `infrastructure/scheduler/` ve `agent/workflows/` katmanlarının somut
  implementasyonudur.
- [[0006-persistans-sqlite-sqlalchemy-imperative-mapping]] — job'lar
  oradaki repository'leri ve `AsyncSession`'ı kullanır.
- _gelecek ADR_ — Notifier kanal seçimi (ADR-0008), agent loop pattern
  (ADR-0009) bu scheduler'la birlikte çalışacak.
