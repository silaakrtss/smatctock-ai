# Demo Akışı — Kooperatif Operasyon Ajanı

Hackathon sunumunda izlenebilecek tek hikâye altında beş temayı birleştiren
demo akışı. Her adım hangi ADR'ı sahnede gösteriyor.

## Hazırlık

1. `.env` dosyasında `MINIMAX_API_KEY` veya `GOOGLE_API_KEY` dolu.
2. `make run` ile sunucu açık. Tarayıcıda iki sekme: `/` ve `/dashboard`.
3. (Opsiyonel) `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` dolu → Telegram
   uygulamasında manager kanalı izlenir.

## Akış

### 1. Stok sorusu (Tema 4)

**Sohbet (`/`):**

> "Düşük stoklu ürünleri listele"

Agent `list_low_stock_products` tool'unu çağırır → `StockService.
find_below_threshold` → eşik altı ürünleri Türkçe özetler.

**ADR kanıtı:** ADR-0009 § 4 (registry + dispatcher), ADR-0006 (SQLite
async sorgu), ADR-0005 § 5 (tool result conversation state'inde korunur).

### 2. Tedarik taslağı (Tema 1 + Tema 4)

**Sohbet:**

> "Domates için 50 adet tedarik taslağı oluştur"

Agent `create_reorder_draft` tool'unu çağırır → `StockService.
create_reorder_draft` → `NotificationService.dispatch` → `FanoutNotifier`:

- `TelegramNotifier` manager chat'ine MarkdownV2 mesajı (varsa)
- `FrontendNotifier` DB'ye kaydeder + `SseHub.publish`

**Sahnede:** Operasyon panelinde `/dashboard` sekmesinde "🔔 Canlı
Bildirimler" sütununa **anında** notification kartı düşer (SSE).

**ADR kanıtı:** ADR-0008 § 1 (fanout paralel), ADR-0008 § 3 (DB + SSE),
ADR-0009 § 5 (write tool business rule application'da).

### 3. Kargo takip (Tema 2 + Tema 3)

**Sipariş Takip (`/order-tracking`):**

Sipariş ID `101` → "Sorgula" → HTMX `GET /orders/101` → sipariş detayı.
Sohbet sekmesinde:

> "101 numaralı siparişin kargo durumu nedir?"

Agent `get_shipment_status` → `ShippingService.get_by_order` → carrier,
tracking number, ETA.

**ADR kanıtı:** ADR-0002 (layered: presentation → agent → application →
domain), ADR-0006 (SQL repository).

### 4. Proaktif tetikleyici (Tema 5)

Scheduler `SCHEDULER_ENABLED=true` ile başlatılırsa, `check_stock_thresholds`
veya `check_shipping_delays` job'ları arka planda eşik / gecikme tespit
edip aynı notification fanout'una düşer — kullanıcı bir şey sormadan.

**ADR kanıtı:** ADR-0007 (APScheduler async, in-process), ADR-0001 § 5
(sabah brifingi + reaktif aksiyon birleşimi).

## Sunum dili — tek cümle

> "Manager kahvesini içerken Telegram'a uyarı düşüyor; aynı dakikada panelde
> bildirim kartı beliriyor; aynı agent reaktif sohbette de tedarik taslağını
> üretebiliyor — beş tema tek bir kooperatif ajanı altında."
