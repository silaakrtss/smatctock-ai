# Kooperatif Operasyon Ajanı

YZTA Hackathon · Tema 1–5'i tek hikâye altında birleştiren proaktif Türkçe agent.

Stok eşiği aşıldığında tedarikçiye taslak hazırlar, kargo gecikince
yöneticiyi uyarır, müşteriye bildirim gönderir; aynı agent reaktif
sohbette stok ve sipariş sorularını yanıtlar.

- 🏗️ 5 katmanlı (domain → application → agent → infrastructure → presentation)
- 🧪 164+ test, %86 coverage, mypy `--strict`, import-linter 7 kontrat
- 🔌 Çift LLM sağlayıcı (MiniMax M2.7 / Gemini Flash) tek port arkasında
- 📡 Telegram + SSE paralel bildirim fanout'u
- 🤖 8 tool'lu agent loop (max 8 iter, `reasoning_details` korunur)
- 📅 11 ADR (mimari kararlar), TDD refactor disiplini

> **Demo akışı:** [`docs/concepts/demo-akisi.md`](docs/concepts/demo-akisi.md)
> · **Mimari kararlar:** [`docs/index.md`](docs/index.md)
> · **TDD checklist:** [`docs/concepts/tdd-refactor-checklist.md`](docs/concepts/tdd-refactor-checklist.md)

---

## Gereksinimler

| Araç | Sürüm | Notu |
|------|-------|------|
| Python | 3.10 veya üstü | `python3 --version` ile kontrol et |
| `pip` + `venv` | standart | sanal ortam kuracaksın |
| Git | herhangi | klonlama için |

API anahtarları:

| Anahtar | Zorunlu? | Yokken davranış |
|---------|----------|------------------|
| `MINIMAX_API_KEY` veya `GOOGLE_API_KEY` | En az birisi | AI chat patlar; geri kalan endpoint'ler çalışır |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Opsiyonel | Telegram notifier **noop** olur; SSE üzerinden bildirimler yine düşer |

> MiniMax key'i [minimax.io](https://www.minimax.io/) (pay-as-you-go),
> Gemini key'i [aistudio.google.com](https://aistudio.google.com/apikey)
> (cömert free tier) üzerinden alınır.

---

## Hızlı Başlangıç (5 adım, ~5 dakika)

### 1. Klonla

```bash
git clone https://github.com/silaakrtss/smatctock-ai.git
cd smatctock-ai
```

> Proje kök dizininin adı klonlanan repo adıdır (`smatctock-ai`). İçeride
> tüm Python kodu `src/` altındadır.

### 2. Sanal ortam + bağımlılıklar

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
make install                       # pip install -e ".[dev]"
```

> **`(.venv)`** prompt'ta görünmüyorsa aktive edilmemiştir; tekrar dene.
> Aktive etmeden `make install` global Python'u kirletir.

### 3. `.env` dosyasını hazırla

```bash
cp .env.example .env
```

`.env`'i aç, **en az** şunu doldur:

```ini
LLM_PROVIDER=minimax              # veya gemini
MINIMAX_API_KEY=sk-cp-...         # eğer LLM_PROVIDER=minimax ise
# GOOGLE_API_KEY=...              # eğer LLM_PROVIDER=gemini ise
```

Tam env değişkenleri listesi: [`.env.example`](.env.example).

### 4. Veritabanını kur ve seed et

```bash
make migrate    # Alembic ile şemayı uygula (data/app.db oluşur)
make seed       # 3 ürün + 3 sipariş + 1 kargo + eşik tanımları
```

Veya tek komutla **bootstrap** (2 + 4 birlikte):

```bash
make bootstrap
```

### 5. Sunucuyu başlat

```bash
make run
```

Açılan URL'ler:

| Sayfa | Adres |
|-------|-------|
| 🏠 Sohbet | <http://127.0.0.1:8000/> |
| 📊 Operasyon paneli | <http://127.0.0.1:8000/dashboard> |
| 📦 Sipariş takip | <http://127.0.0.1:8000/order-tracking> |
| ❤️ Sağlık | <http://127.0.0.1:8000/health> |

İlk denemen için sohbet kutusuna: **"Düşük stoklu ürünleri listele"**.

---

## Sayfalar (ADR-0010)

HTMX + Alpine.js + Tailwind CDN, build pipeline yok. Custom palette:
harvest yeşili + ember turuncusu + cream — kooperatif/tarım çağrışımı.

| Sayfa | Rol | Etkileşim |
|-------|-----|-----------|
| `/` | Yönetici sohbeti | Alpine fetch → `/ai-chat` → agent loop. Mesajlar markdown render edilir (tablo, kalın). Sekme geçişlerinde sohbet **sessionStorage**'da kalır. |
| `/dashboard` | Operasyon paneli | HTMX `/products` + `/orders` tabloları; sağda SSE üzerinden canlı bildirim kartları. Sekme arkaya gidince SSE kapanır, öne gelince yeniden bağlanır. |
| `/order-tracking` | Sipariş takibi | Sipariş ID → `/orders/{id}` HTMX swap |

---

## 5 Tema → Kod Haritası

ADR-0001 PDF'in 6 temasından 5 tanesi kapsam içinde (Tema 6 analitik
**kapsam dışı**, ADR-0001 TL;DR):

| # | Tema | Bu projedeki karşılığı |
|---|------|------------------------|
| **1** | Müşteri İletişimi Otomasyonu | `notify_customer` tool · `FanoutNotifier` (Telegram + SSE) · `NotificationService.notify_customer` |
| **2** | Ürün ve Sipariş Takibi | `/products`, `/orders/{id}` · `get_order_status`, `list_orders` tool · `OrderService` |
| **3** | Kargo Süreçlerinin Yönetimi | `Shipment` entity · `check_shipping_delays` job · `get_shipment_status`, `list_delayed_shipments` tool |
| **4** | Stok ve Envanter Yönetimi | `StockThreshold` · `check_stock_thresholds` job · `get_product_stock`, `list_low_stock_products`, `create_reorder_draft` tool |
| **5** | İş Akışı ve Görev Yönetimi | APScheduler · `morning_briefing` agent workflow · proaktif tetikleyiciler |

Agent'ın 8 tool'u tek yerde: [`src/agent/tools/definitions.py`](src/agent/tools/definitions.py).

---

## İki sağlayıcılı LLM (port arkasında)

`LLM_PROVIDER=minimax` (varsayılan) veya `LLM_PROVIDER=gemini`. Composition
root env'e göre adapter bağlar; üst katmanlar yalnızca `LLMClient` portunu
görür. **Otomatik runtime fallback yok** — sağlayıcı seçimi statik
(ADR-0005 § 3).

Yeni sağlayıcı eklemek = `src/infrastructure/llm/` altına bir adapter +
composition root'ta DI binding.

---

## Scheduler (opsiyonel)

```ini
SCHEDULER_ENABLED=true
SCHEDULER_STOCK_CHECK_CRON=0 * * * *      # saat başı
SCHEDULER_SHIPPING_CHECK_CRON=0 * * * *
SCHEDULER_MORNING_BRIEFING_CRON=0 8 * * * # her sabah 08:00
```

Devreye alınınca `lifespan` şu job'ları kayıt eder:

- `check_stock_thresholds` — eşik altı ürünler için bildirim
- `check_shipping_delays` — gecikmiş kargolar için manager uyarısı

Demo'da scheduler kapalı tutmak daha güvenli — proaktif aksiyonu
arkadan değil **chat'ten** tetikleyerek göstermek daha okunabilir.

---

## Geliştirme

```bash
make check        # ruff + format + mypy --strict + import-linter + pytest
make test         # sadece test
make lint         # ruff check
make typecheck    # mypy --strict src/
make imports      # lint-imports (7 katman/sızıntı kontratı)
make reset-db     # DB'yi sıfırla → migrate → seed (demo prova için)
```

CI'da hepsi zorunlu (`.github/workflows/ci.yml`). Coverage eşiği **%85**
(ADR-0002).

### Klasör yapısı

```
src/
  domain/          # Saf iş kuralları (dataclass, framework yok)
  application/     # Use case'ler + port arayüzleri
    ports/         # Repository, LLMClient, Notifier, Scheduler
    services/      # StockService, OrderService, ...
  agent/           # Tool-calling loop, registry, dispatcher
    tools/         # 8 tool tanımı + handler binding'leri
    prompts/       # Markdown sistem promptları
    workflows/     # morning_briefing vb. proaktif akışlar
  infrastructure/  # Port implementasyonları (composition root burada)
    db/            # SQLAlchemy async + imperative mapping (ADR-0006)
    llm/           # MiniMax / Gemini (ADR-0005)
    notifiers/     # Telegram, SSE hub, Fanout (ADR-0008)
    scheduler/     # APScheduler async (ADR-0007)
  presentation/    # FastAPI + Jinja2
```

Bağımlılık yönü: `presentation → agent → application → domain`.
`infrastructure` yalnızca composition root'tan instantiate edilir.
İhlaller `lint-imports` ile CI'da yakalanır.

---

## Sorun Giderme

**`/dashboard` boş, "Henüz bildirim yok" yazıyor.**
Henüz bildirim üretilmediği için doğru — sohbet kutusundan
*"Domates için 50 adet tedarik taslağı oluştur"* yaz. Dashboard'da
yeni kart anında belirmeli.

**Sohbette `<think>...</think>` görünüyor / markdown render olmuyor.**
Bu sürümde sanitize edilir ve markdown render edilir. Tarayıcı cache
yüzünden eski sürüm yüklenmiş olabilir; `Ctrl+Shift+R` ile sert
yenileme dene.

**`OperationalError: no such table: products`.**
`make migrate` çalıştırılmamış. Yukarıdaki 4. adımı izle.

**Sohbet sekmeyi değiştirince siliniyor.**
Aynı sekmede değişiklik geçişlerinde `sessionStorage`'da kalır. Tarayıcı
sekmesini kapatıp tekrar açtığında — yeni sekme/oturum demektir, geçmiş
silinir (beklenen davranış).

**LLM kotası doldu (HTTP 503).**
Adapter 3 deneme exponential backoff yapıp `LLMRateLimitError` fırlatır.
Birkaç dakika bekle veya `LLM_PROVIDER=gemini`'a geç (free tier cömert).

**LLM çağrı geçmişini inceleme.**
`logs_llm/YYYY-MM-DD.jsonl` her LLM çağrısının request + response'unu
içerir (içsel debug için). Dosyalar `.gitignore`'dadır.

---

## ADR (Architecture Decision Records)

Mimari kararları `docs/decisions/` altında tutuyoruz; yönetim için
[`adr-kit`](https://github.com/saadettinBerber/adr-kit) Claude Code plugin'i.

```
/plugin marketplace add saadettinBerber/adr-kit
/plugin install adr-kit@adr-kit
```

Komutlar:

| Komut | Ne yapar |
|-------|----------|
| `/adr-kit:adr-new <başlık>` | Yeni ADR + otomatik numara + index'e satır |
| `/adr-kit:adr-install-claude-md` | CLAUDE.md'ye ADR disiplin bloğu |

Mevcut 11 ADR: [`docs/index.md`](docs/index.md).

---

## Daha fazla oku

- [`docs/concepts/demo-akisi.md`](docs/concepts/demo-akisi.md) —
  sunumda izlenebilecek tek hikâye, beş tema adım adım
- [`docs/concepts/tdd-refactor-checklist.md`](docs/concepts/tdd-refactor-checklist.md) —
  Red→Green→Refactor 5 maddelik hızlı tarama
- [`CLAUDE.md`](CLAUDE.md) — projenin AI asistana verdiği talimatlar
- [`docs/decisions/`](docs/decisions/) — 11 ADR (hepsi Türkçe, TL;DR'lı)
