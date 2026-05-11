# Debug: Frontend Davranışları

Bu sayfa tarayıcı, sayfa render, Alpine state, SSE bağlantısı ve
HTMX swap konularındaki sorunları toplar.

İlgili ADR: [ADR-0010 Frontend — HTMX + Alpine + Tailwind](../decisions/0010-frontend-htmx-alpine-tailwind.md).

---

## Dashboard'da bildirim kartı görünmüyor / takılı kalıyor

**Sebep adayları:**

1. **Hiç bildirim üretilmedi.** Yeni kurulumda DB temiz, sohbetten
   tedarik draft veya müşteri bildirimi tetiklenmediyse boş — bu
   **doğru davranış**. "Henüz bildirim yok" yazısı görünür.
2. **SSE bağlantı sızıntısı** (önceki sürüm). Sekmeler arası gezindikten
   sonra HTTP/1.1 per-origin bağlantı limiti doluyordu. Fix: `5aa9865`
   ve `0e756a6` commit'leri sonrası. Eğer hala takılıyorsa tarayıcı
   cache'ini temizle (`Ctrl+Shift+R`).
3. **Browser console'da JS hatası.** F12 → Console sekmesi — Alpine
   veya DOMPurify yüklenememiş olabilir (CDN engelli ağ).

**Doğrulama:** Server tarafında `curl http://127.0.0.1:8000/notifications`
boş `[]` dönerse hiç bildirim yok; doluysa frontend tarafı sorunlu.

**Tedarik draft akışı:**

```
Sohbet kutusu → "Domates için 50 adet tedarik taslağı oluştur"
   ↓
AI agent `create_reorder_draft` tool'unu çağırır
   ↓
StockService.create_reorder_draft → NotificationService.dispatch
   ↓
FanoutNotifier → FrontendNotifier (DB save + SseHub.publish)
                + TelegramNotifier (varsa)
   ↓
Dashboard SSE event al, Alpine notifications listesine unshift
```

---

## Sohbet sekmeyi değiştirince siliniyor

**Sebep:** Aynı sekmedeki sayfa geçişlerinde mesajlar `sessionStorage`'da
korunur. Tarayıcı sekmesi kapatıldığında veya yeni sekme açıldığında
**yeni bir oturum** olur, geçmiş silinir. Bu **beklenen davranış**.

**Çözüm:** Aynı sekmede kalarak gezin. Birden fazla sekme açtıysan
her birinin kendi geçmişi olur.

**Geçmişi manuel temizle:** Sohbet sayfasında sağ üstte "Geçmişi temizle"
butonu (sadece mesaj varken görünür).

**Kalıcı tutmak istiyorum:** ADR-0009 § Kısıtlar emrediyor:
*"/ai-chat iki çağrısı arasında geçmiş paylaşılmaz."* Bu **mimari
karar**; değiştirmek için yeni ADR gerekir. Hackathon kapsamı için
kabul edildi (multi-turn chat ihtiyacı doğarsa ayrı ADR).

`sessionStorage` yerine `localStorage` tercih edilebilir (`chat.html`
içinde `CHAT_STORAGE_KEY` aynı, sadece API değişir) — kişisel kullanımda
mantıklı, demo'da temiz başlangıç için sessionStorage daha güvenli.

---

## Markdown render olmuyor (yanıtta `|` ve `**` görünüyor)

**Sebep:** Tarayıcı cache veya marked.js / DOMPurify CDN'i yüklenememiş.

**Çözüm:**

1. **Sert yenileme:** `Ctrl+Shift+R` (Windows/Linux) veya
   `Cmd+Shift+R` (Mac) — tarayıcı cache'ini atlar.
2. **F12 → Network:** `marked.min.js` ve `purify.min.js` 200 dönüyor mu?
   Engellenmişlerse adblocker / VPN / kurumsal proxy CDN'i engelliyor
   olabilir. Geçici çözüm: bu script'leri lokal `static/js/`'e indir.
3. **Sürüm doğrulaması:** `git log --oneline | grep marked` —
   `78d0b29` (F9.3 markdown render) merge edilmiş olmalı.

**Mimari not:** Yalnızca **assistant** mesajları markdown render eder;
user mesajları `x-text` ile XSS'e karşı düz metin gösterilir. DOMPurify
bir ek güvenlik katmanı.

---

## SSE keepalive ping'leri ile sürekli istek yapıyor sanıyorum

**Sebep:** Server her 15 saniyede `: keepalive\n\n` gönderir bağlantı
canlılığını korumak için. Bu **yeni request değil** — aynı bağlantı
üzerinden tek satırlık SSE comment.

**Doğrulama:** F12 → Network → `notifications/stream` satırı —
**bir tane** olmalı, status `(pending)` ve giderek büyüyen response
size görünür.

---

## "Bağlantı kuruluyor..." sürekli görünüyor

**Sebep:** `EventSource.onerror` tetiklenmiş; sunucu bağlantıyı kapattı
veya proxy ara sunucu (nginx/cloudflare) SSE'yi tampona alıyor.

**Çözüm:**

1. **Sunucu loglarını kontrol et:** `make run`'ın çalıştığı terminalde
   exception var mı?
2. **Doğrudan curl ile test:**
   ```bash
   curl -N http://127.0.0.1:8000/notifications/stream
   ```
   `: keepalive` satırları akıyorsa server tarafı sağlam, problem
   browser'da. Akmıyorsa server tarafı incelenmeli.
3. **Reverse proxy varsa:** `proxy_buffering off` ve `proxy_read_timeout`
   yüksek olmalı (nginx için). Hackathon ölçeğinde doğrudan uvicorn
   kullanılır, bu durum gelmez.

---

## "Geçmişi temizle" butonu görünmüyor

**Sebep:** Sohbette henüz mesaj yok. Buton `x-show="messages.length > 0"`
ile koşullu — boş sohbette gereksiz olduğu için gizli.

**Çözüm:** En az bir mesaj yaz, buton sağ üstte belirir.

---

## Sayfa görseli bozuk — renkler default Tailwind'e dönmüş

**Sebep:** `tailwind.config.theme.extend.colors` block'u CDN tarafından
parse edilemedi (JS hatası), default palette devreye girdi.

**Doğrulama:** F12 → Console — Tailwind config hatası var mı?

**Çözüm:** `base.html` içindeki `tailwind.config = {...}` block'u inline
çalışmalı, başka script onu override etmemeli. Eğer custom.css'in
override'ları çalışmıyorsa: `/static/css/custom.css` 200 dönüyor mu
(F12 → Network) kontrol et.

---

## HTMX swap çalışmıyor (sipariş takip sayfasında)

**Sebep:** HTMX kütüphanesi yüklenmedi, ya da `hx-target` selector'ü
DOM'da yok.

**Doğrulama:**

1. F12 → Console: `htmx` global'i tanımlı mı? (`window.htmx` deneyin)
2. F12 → Network: `htmx.org@1.9.12` 200 dönüyor mu?
3. `#order-result` div'i HTML'de mi?

Geçici fallback: tarayıcı doğrudan `http://127.0.0.1:8000/orders/101`'e
gidip JSON cevabı görebilir.
