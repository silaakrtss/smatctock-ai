# ADR 0010: frontend-htmx-alpine-tailwind

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Frontend **HTMX + Alpine.js + Jinja2 (FastAPI native) + Tailwind
> CSS** üzerine kurulur; hepsi **CDN** üzerinden yüklenir, build pipeline
> yoktur. Sayfa mimarisi **multi-page**: `/` (chat), `/dashboard` (manager),
> `/order/{id}` (müşteri takip). SSE bildirimleri HTMX'in native
> `hx-ext="sse"` extension'ı ile tüketilir. Tasarım **custom Tailwind palette**
> (kooperatif/tarım çağrışımı: yeşil + turuncu + cream) ve **custom
> component katalog** ile yapılır; generic AI aesthetic (shadcn vibe, default
> DaisyUI) yasaklanır. Manager/müşteri ayrımı **URL bazlı simülasyon** —
> hackathon kapsamında auth yok. Mevcut `static/index.html` bu ADR ile
> yeniden yazılır ve `src/presentation/templates/`'a taşınır.
>
> **Kapsam:** `src/presentation/templates/`, `src/presentation/static/` (CSS,
> partial JS), `src/presentation/api/routes/` altındaki HTML render
> endpoint'leri. Backend tek `uvicorn` süreçte sunar; ayrı frontend süreç,
> ayrı build çıktısı, ayrı deploy yok.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **Build pipeline yasak.** Vite, webpack, esbuild, parcel, rollup, turbo —
>   hiçbiri kurulmaz. CDN'den yüklenen `htmx.min.js`, `alpine.min.js`,
>   `tailwindcss` script'leri dışında JS/CSS bundling yapılmaz.
> - **React / Vue SFC / Svelte / Solid yasak.** Bu ölçek için overkill;
>   build pipeline yasağıyla zaten uyumsuz.
> - **Generic AI aesthetic yasak.** Default shadcn, default DaisyUI, "Cursor
>   IDE clone'u" gibi tipik AI-generated UI tarzları kullanılmaz. Custom
>   palette + custom component katalog şarttır.
> - **Frontend backend'den ayrı uygulama değildir.** Tek `uvicorn` süreç
>   hem API hem HTML render eder; ayrı dev server, ayrı port, reverse proxy
>   yasak.
> - **Auth bu ADR kapsamı dışıdır.** `/dashboard` ve `/order/{id}` doğrudan
>   URL ile erişilebilir. Production auth gerekirse ayrı ADR.
> - **Single-page state yönetimi yasak** (Redux/Zustand benzeri).
>   Server-rendered partial swap (HTMX) + lokal etkileşim (Alpine `x-data`)
>   yeterli; client-side global state yok.
> - **Inline `<style>` blokları minimum tutulur.** Tüm stil Tailwind
>   utility'lerinde veya `static/css/`'deki dosyalarda yaşar; sayfa içi
>   stil yalnızca dinamik durum (renk kodu vb.) için izinli.
> - **JavaScript dosyaları `presentation` katmanı dışında oluşturulamaz.**
>   `static/js/` Alpine component'leri ve SSE bağlama gibi yardımcılar
>   için sınırlı kullanılır.

## Context

ADR-0001 beş tema (1, 2, 3, 4, 5) seçildi; ADR-0008 SSE notifier kararı
verildi; ADR-0009 reaktif chat agent loop'u tanımlandı. Demo başarısının
büyük kısmı **frontend görünürlüğünden** geliyor — backend mükemmel olsa
bile jüri ekranda görmediğini puanlayamaz.

Mevcut durum:
- `static/index.html` mount edilmiş (137-satırlık `main.py`'da `app.mount("/static", ...)`);
  içeriği bilinmiyor ama muhtemelen placeholder.
- Hiçbir HTML template motoru yok.
- ADR-0008 SSE endpoint'i (`/notifications/stream`) tüketici frontend bekliyor.
- ADR-0009 `/ai-chat` reaktif endpoint'i için chat UI yok.

Kısıtlar:

1. **Sıfır maliyet, sıfır deploy karmaşıklığı** (önceki ADR'ların ruhu) —
   ek build server, dist klasörü, reverse proxy istemeyiz.
2. **Demo görsel etkisi yüksek olmalı** — jüri "modern, profesyonel ama
   bir AI değil insan tasarladı" hissi almalı; "generic AI aesthetics"
   (shadcn-vibe, default Tailwind purple) sunumu zayıflatır.
3. **Mimari iddia ile tutarlı** — ADR-0002'nin "presentation composition
   root" kuralı, frontend'in de tek süreçte yaşamasını gerektiriyor.
4. **Üç ekran ihtiyacı net**:
   - Chat (Tema 1 müşteri agent'ı)
   - Manager dashboard (Tema 2 + Tema 4 + Tema 5)
   - Müşteri sipariş takip (Tema 1 + Tema 3, SSE ile canlı durum)
5. **Hackathon süresi** — kurulum + 3 ekran + chat + SSE entegrasyonu
   makul süre içinde tamamlanabilir olmalı.

PDF "teknik olarak serbest" diyor; frontend stack kararı net bir ADR
gerektirir çünkü sonraki katılımcı/incelemeci "neden React değil?"
sorusunun yazılı cevabını isteyecek.

## Decision

### 1. Stack

| Katman | Teknoloji | Yükleme |
|--------|-----------|---------|
| Template motoru | **Jinja2** | FastAPI native (`fastapi[jinja2]` veya `jinja2`) |
| HTML over-the-wire | **HTMX 2.x** | CDN (`<script src="https://unpkg.com/htmx.org@2">`) |
| Lokal client state | **Alpine.js 3.x** | CDN |
| CSS framework | **Tailwind CSS** | CDN (Play CDN, no JIT build) |
| SSE | HTMX SSE extension | CDN (`hx-ext="sse"`) |

Notlar:
- Tailwind Play CDN production'da önerilmiyor ancak hackathon ölçeği +
  build pipeline yasağı için kabul edilebilir trade-off. Post-hackathon
  production gerekirse ayrı bir ADR ile Vite + Tailwind JIT eklenebilir.
- `jinja2` paketi `pyproject.toml`'a eklenir.

### 2. Klasör yapısı

```
src/presentation/
  main.py                          # FastAPI app, composition root
  templates/                       # Jinja2 templates
    base.html                      # Layout: head, nav, footer, SSE bootstrap
    components/                    # Kısmi (partial) parçalar
      chat_bubble.html
      order_card.html
      notification_toast.html
      stock_badge.html
    pages/
      home.html                    # `/` — Chat sayfası
      dashboard.html               # `/dashboard` — Manager
      order_detail.html            # `/order/{id}` — Müşteri takip
  static/
    css/
      app.css                      # Tailwind base + custom utilities
    js/
      chat.js                      # Chat input, agent cevap render
      sse_bootstrap.js             # SSE bağlantısı, toast handler
  api/
    routes/
      pages.py                     # HTML render route'ları (Jinja)
      chat.py                      # /ai-chat (ADR-0009)
      notifications.py             # /notifications + /notifications/stream (ADR-0008)
      products.py
      orders.py
```

### 3. Sayfa mimarisi (multi-page)

#### 3.1 `/` — Chat sayfası
- Üst nav: logo + "Dashboard"a link + bildirim zili
- Orta: chat container, kullanıcı mesajı sağda, agent solda
- Tool çağrıları **görünür** kutucuk olarak gösterilir (Demo'da agent
  reasoning'i şeffaf):
  ```
  [🔧 list_orders(customer_name="Ayşe") çağrılıyor...]
  [📊 Sonuç: 2 sipariş bulundu]
  ```
- Alt: input + gönder butonu. Enter ile gönderim.
- Etkileşim: form HTMX ile `/ai-chat`'e POST; cevap partial template
  olarak chat container'a `hx-swap="beforeend"` ile eklenir.
- Loading state: HTMX `htmx:beforeRequest` event'inde loading dots göster.

#### 3.2 `/dashboard` — Manager
- Üç kart sıralanmış, responsive grid:
  - **Bugünkü Siparişler** — sayı + kısa liste (ilk 5)
  - **Düşük Stok** — eşik altı ürünler
  - **Gecikmiş Kargolar** — gecikme sayısı + liste
- Sağda dikey timeline: **Canlı Bildirimler** (SSE)
- Her kart `hx-get` ile partial endpoint'i çağırır; sayfa yüklenirken
  ilk durum render, sonra `hx-trigger="every 30s"` ile yenilenir (veya
  SSE'den ilgili kategori event'i geldiğinde `hx-trigger="sse:..."`).

#### 3.3 `/order/{id}` — Müşteri sipariş takip
- Üst: sipariş özeti (ID, müşteri, kalemler, toplam)
- Orta: kargo timeline (Hazırlanıyor → Kargoda → Yolda → Teslim)
- Alt: bu sipariş için son bildirimler (`NotificationLog`'dan)
- SSE: `recipient` `CustomerRecipient(order_id=...)` olan event'lerde
  toast göster + timeline güncelle.

### 4. SSE entegrasyonu

HTMX SSE extension ile native. Base template'de:

```html
<body hx-ext="sse" sse-connect="/notifications/stream">
  ...
  <div sse-swap="notification" hx-swap="afterbegin"
       hx-target="#notification-timeline"></div>
</body>
```

Backend SSE event şu formatta yayar:

```
event: notification
data: <div class="...">🔴 Domates stoğu kritik (40 kg)</div>

```

Bu sayede frontend'de **JavaScript yazmadan** SSE bildirimleri DOM'a
düşer. Toast animasyonu Tailwind transition + Alpine `x-transition`
ile yapılır.

### 5. Tasarım yaklaşımı

#### 5.1 Felsefe
- **Modern, profesyonel, mütevazi** — Stripe-steril değil, Bootstrap-default
  da değil.
- **Domain çağrışımı**: kooperatif/tarım → doğa renkleri.
- **Yoğun beyaz alan**, okunaklı tipografi, az ama anlamlı animasyon.
- **frontend-design skill çağrılır** ilk template implementasyonunda;
  ADR-0010 sınırları içinde production-grade çıktı üretir.

#### 5.2 Renk paleti
- **Birincil yeşil**: `#3F7B5C` (toprak/yaprak — Tailwind `emerald-700`
  yakını ama özelleştirilmiş)
- **Vurgu turuncu**: `amber-600` (hasat, sıcaklık)
- **Nötr cream/beige**: `stone-50` / `stone-100` (arka plan)
- **Hata**: `red-600`
- **Uyarı**: `amber-500`
- **Başarı**: birincil yeşil
- **Karanlık mod**: opsiyonel; stretch goal, kapsamda zorunlu değil.

#### 5.3 Tipografi
- **Tek font ailesi**: Inter veya Plus Jakarta Sans (Google Fonts CDN).
- **Başlık ağırlıkları**: 600 / 700.
- **Body**: 400.
- **Code/Tool çağrıları**: JetBrains Mono.

#### 5.4 Bileşen kataloğu (custom)
Hepsi `templates/components/` altında, Tailwind utility'leri ile:

- **Chat bubble** (kullanıcı / agent / tool result varyantları)
- **Order card** (sipariş özeti)
- **Product card** (ürün + stok bar)
- **Stock badge** (yeşil/turuncu/kırmızı kategorisine göre)
- **Notification toast** (kategori emoji + başlık + body)
- **Empty state** (resimsiz, ikonlu)
- **Loading dots** (chat agent düşünürken)
- **Status pill** (sipariş/kargo durumu)

Generic shadcn `Button`, `Card` import'ları yapılmaz; her bileşen
domain'in görsel diline uyarlanır.

### 6. Manager / Müşteri rol ayrımı

- **Hackathon kapsamında auth yok.**
- `/dashboard` URL'i girince manager view; `/order/{id}` URL'i girince
  müşteri view.
- Demo sırasında jüri her iki rolü farklı URL'lerle gezerek görür.
- SSE topic ayrımı: `FrontendNotifier` (ADR-0008) recipient tipine göre
  event metadata'sı ekler (`manager` vs `customer:order_id`); frontend
  ilgili topic'leri filtreler.

### 7. Tarayıcı desteği

- Chrome 110+, Firefox 110+, Safari 16+ — modern evergreen.
- IE / eski Edge yasak (zaten ölü).
- Mobile responsive **istenir** (Tailwind responsive utilities ile);
  ama jüri muhtemelen masaüstünde gösterecek, mobil pixel-perfect
  olmayabilir.

### 8. Performans

- Tailwind Play CDN ~3MB JS yükü; hackathon ölçeği için kabul.
- HTMX + Alpine + Tailwind toplam ~120KB gzip (Tailwind hariç) — modest.
- Initial paint < 1s hedef (lokal demo'da kolay).
- SSE bağlantısı tek; pollutant değil.

### 9. Erişilebilirlik (a11y)

- Form input'larına `<label>` zorunlu.
- Buton'larda `aria-label` gerekirse.
- Renk kontrastı WCAG AA hedef (yeşil + cream uyumlu).
- Klavye navigasyonu (Tab) çalışır.
- Stretch: screen reader testi (hackathon kapsamında zorunlu değil).

### 10. Test stratejisi

ADR-0002 ile uyumlu:

- **E2E** (`tests/e2e/api/`): FastAPI `TestClient` ile sayfa render'ı
  doğrulanır — HTML response 200 ve içerikte beklenen marker'lar.
- **HTMX partial endpoint testleri**: `GET /dashboard/today-orders/partial`
  gibi parça endpoint'leri her dosya için bir test.
- **SSE E2E**: ADR-0008'de tanımlı; frontend tarafı manuel veya stretch
  Playwright.
- **Manuel demo provası**: scripted senaryo — kullanıcı sorusu, scheduler
  tetikleme, bildirim parlama, dashboard güncelleme.
- `webapp-testing` skill (Playwright) stretch goal; hackathon kapsamında
  manuel yeterli.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **Vite + React + TypeScript + Tailwind** | Modern ve güçlü; ancak build pipeline + dist + dev server + reverse proxy üçlüsü hackathon demo'yu kırılgan yapar. Tek `uvicorn` süreç ilkesi bozulur. Aynı süre içinde HTMX daha çok ekran üretir. |
| **Vue 3 SFC (build'siz CDN modu)** | Vue 3'ün CDN modu Options API ile çalışır; setup syntax build gerektirir. Reactivity için Alpine.js daha hafif ve hackathon-dostu. |
| **Svelte** | Build pipeline (Vite/SvelteKit) zorunlu; React ile aynı kurulum yükü. |
| **Vanilla JS + Tailwind CDN** | Sıfır framework; ancak chat + SSE + dashboard + form state için 500+ satır manuel DOM kodu gerekir. HTMX + Alpine bu işin %80'ini deklaratif olarak çözer. |
| **Bootstrap 5 + jQuery** | Generic, eski, hackathon görsel etkisi zayıf. Tailwind utility-first daha modern. |
| **DaisyUI (Tailwind component library)** | Generic AI aesthetic tuzağı — jüri "shadcn template" hissi alır. Custom component katalog daha güçlü iddia. |
| **shadcn/ui** | React'e bağlı; build pipeline zorunlu. Ayrıca aşırı tanınmış görünüm. |
| **Multi-page yerine SPA (HTMX `hx-boost` ile)** | Tek HTML, partial swap; URL korunur ama back button davranışı edge case'lerde sorunlu. Multi-page daha güvenli ve URL paylaşılabilirlik bonus. |
| **Tek sayfa + tab'lar** | URL paylaşılabilirlik kayıp; demo'da "şu URL'i aç" diyemeyiz. |
| **Auth (oturum yönetimi)** | Hackathon kapsamı dar; demo'da rol simülasyonu yeterli. Auth ayrı bir ADR. |
| **WebSocket** | SSE zaten bizim için yeterli (sunucudan istemciye tek yönlü). WebSocket çift yönlü, daha karmaşık; ADR-0008'de zaten reddedildi. |
| **Tailwind JIT build (CLI ile pre-compile)** | Daha sağlıklı production; ancak build adımı yasağı (felsefe gereği). Play CDN trade-off. |
| **Inline `<style>` ile custom CSS** | Bakım borcu; Tailwind utility yaklaşımı daha disiplinli. |
| **Karanlık mod ilk sürümde zorunlu** | Hackathon kapsamı için fazla; ışık modu yeterli, karanlık stretch goal. |
| **Manuel JavaScript SSE (`new EventSource`)** | HTMX SSE extension daha az kod; sayfa içi DOM manipülasyonu deklaratif. |

## Consequences

### Olumlu

- **Sıfır build, tek deploy** — `uvicorn main:app` ile her şey çalışır.
  Demo kurulumu basit, kırılganlık düşük.
- **Demo görsel etkisi yüksek** — 3 sayfa + canlı SSE + custom tasarım
  jüriye "ürün" hissi verir.
- **Mimari iddia güçlü**: "HTMX = modern hypermedia, build pipeline'sız
  full-stack" hikâyesi sunumda mimari disiplinin (ADR'ların) doğal
  uzantısı olarak anlatılır.
- **frontend-design skill ile generic AI aesthetic tuzağından kaçınma**
  yazılı bir kural; uygulama disiplinle yapılır.
- **HTMX SSE native** → ADR-0008 SSE kararını **bir attribute** ile
  tüketir; backend ve frontend arasındaki entegrasyon yüzeyi minimum.
- **Multi-page + URL paylaşılabilirlik** demo'da jürinin "şu URL'i bir
  aç" demesini kolaylaştırır.
- **Tek dil pipeline'ı** (Python + HTML/CSS) — ekip frontend için ayrı
  build/test/lint zinciri öğrenmek zorunda kalmaz.

### Olumsuz

- **Tailwind Play CDN production'a uygun değil** — JIT runtime'da
  yapılır, performans/file size optimum değil. Hackathon kapsamında
  kabul; post-hackathon ayrı ADR ile Tailwind CLI/Vite eklenir.
- **HTMX paradigmasına aşinalık gerekir** — React zihniyetinden gelen
  geliştirici için ilk saatler sürtünmeli olabilir. Karşılığında
  toplam kod miktarı daha az.
- **SPA hissi yok** — sayfalar arası geçişte browser-grade refresh
  görünür (HTMX `hx-boost` ile yumuşatılabilir; stretch goal).
- **State client'ta yok** — undo, optimistic update gibi pattern'ler
  zorlaşır. Hackathon kapsamında bu tür ileri etkileşim gerekmiyor.
- **Auth yokluğu** demo'da "herkes her şeyi görebiliyor" eleştirisini
  davet edebilir; cevabı: kapsam dışı, ayrı ADR.
- **Tasarım disiplini gevşerse generic AI aesthetic'e kayma riski**
  yüksek; bu yüzden frontend-design skill ile başlamak şart.

## Open items

- [x] `pyproject.toml` bağımlılığı: `jinja2>=3.1`. *(F1.2)*
- [x] `templates/` + `static/` iskeleti. *(F8.5)*
- [x] `base.html` layout. *(F8.5 — HTMX 1.9 + Alpine 3 + Tailwind CDN + Google Fonts Inter/Plus Jakarta Sans; F9.3'te marked + DOMPurify CDN eklendi)*
- [x] 3 sayfa: chat, dashboard, order tracking. *(F8.6 — `chat.html`, `dashboard.html`, `orders_explorer.html`)*
- [x] `static/css/custom.css`: custom palette + tipografi + bileşen stilleri. *(F8.5 — harvest yeşili + ember turuncusu + cream; notification-card animasyon, chat-message bubble, status-pill, F9.3'te markdown-body stilleri eklendi)*
- [x] Chat form submit + cevap render. *(F8.6 inline Alpine x-data; F10.3'te `chatPanel()` function'a çıkarıldı, sessionStorage entegre edildi)*
- [x] `api/routes/pages.py`. *(F8.6 — Jinja2Templates ile 3 endpoint)*
- [x] FrontendNotifier SSE event payload. *(F7.6 + F8.4 — `_serialize` fonksiyonu; event metadata Alpine x-data'da filtrelenebilir formatda)*
- [x] `vectors.db` silme + `static/index.html` kaldırma. *(F1.1, PR #4)*
- [x] Manuel demo provası. *(F9 demo provası — canlı MiniMax çağrısı, 3 pürüz tespit edilip düzeltildi; `docs/concepts/demo-akisi.md` scripted senaryo)*
- [ ] Bileşen kataloğu (components/ altında). *(Bileşenler inline `chat.html`/`dashboard.html` içinde yaşıyor; ayrı `components/` Jinja2 macro paketi çıkarılmadı. Yeni sayfa eklenirse refactor gerekir.)*
- [ ] HTMX partial endpoint'leri. *(`/products` + `/orders` JSON endpoint'leri dashboard'da HTMX target oluyor; ayrı `/partial` route'ları (HTML fragment) eklenmedi — Alpine x-data tarafı JSON parse'ı tercih edildi.)*
- [ ] `static/js/chat.js` ve `sse_bootstrap.js` ayrı dosyalar. *(JS template içinde inline; ileride büyürse `static/js/`'e çıkarılabilir.)*
- [ ] `frontend-design` skill çağrısı. *(El ile palette ve component yazıldı; production-grade tasarım için skill ile cilalama yapılmadı — düşük öncelik, mevcut UI ADR-0010 § custom aesthetic kuralını sağlıyor.)*
- [ ] **Stretch**: Playwright E2E test, karanlık mod toggle, mobil responsive son ayar. *(Üçü de stretch goal — kapsamda zorunlu değil, hackathon ölçeği için ertelendi.)*

## Affected areas

- `src/presentation/templates/` — yeni klasör, tüm HTML burada.
- `src/presentation/static/` — CSS ve sınırlı JS.
- `src/presentation/api/routes/pages.py` — yeni dosya, HTML render
  endpoint'leri.
- `src/presentation/api/routes/notifications.py` — ADR-0008 SSE
  endpoint'i bu ADR ile **HTML fragment** payload'a uyarlanır (JSON
  yerine HTMX uyumlu `<div>` parçaları).
- `src/presentation/main.py` — Jinja2 template engine kurulumu, static
  mount, route binding.
- `static/index.html` (kök) — silinir; içerik `templates/`'a taşınır.
- `pyproject.toml` — `jinja2` bağımlılığı.
- [[0001-hackathon-kapsami-temalar]] — bu ADR Tema 1, 2, 3, 4, 5'in
  görsel kanıtını sağlar.
- [[0002-mimari-yaklasim-layered-agent]] — bu ADR oradaki
  `presentation/` katmanını HTML render rolüyle genişletir.
- [[0008-notifier-telegram-frontend-sse]] — bu ADR oradaki SSE
  endpoint'inin HTMX uyumlu HTML fragment dönmesini gerektirir.
- [[0009-agent-loop-tool-calling]] — bu ADR `/ai-chat` cevabını render
  edecek chat UI'ı tanımlar.
- _gelecek ADR_ — auth (gerekirse), Tailwind JIT/Vite (production
  gerekirse), karanlık mod (kullanıcı istekse).
