# ADR 0012: adr-yasam-dongusu-disiplini

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Her PR merge edilmeden önce ilgili ADR'ların **"Open items"**
> bölümü mevcut koda göre güncellenmiş olmalı. Tamamlanan maddeler `[x]`
> olarak işaretlenir ve **kısa bir referansla** (faz, PR numarası veya
> commit hash) zenginleştirilir — silinmez, geçmiş izlenebilir kalır.
> Tamamlanmayan ama bilinçli olarak ertelenen maddeler **`[ ]` olarak
> kalır** ve **neden açık olduğunu açıklayan kısa bir not** eklenir.
> Bu disiplin CLAUDE.md `### 5. ADR` bölümünde yazılıdır ve AI asistan
> her PR kapanışında refleks haline getirir.
>
> **Kapsam:** Tüm ADR'lar (`docs/decisions/`). Bu disiplin yalnızca
> "Open items" bölümünü etkiler; "Decision", "Context", "Alternatives"
> bölümleri ADR'ın immutable yapısı gereği değişmez.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **`[x]` işaretlenirken referans şart.** Çıplak `[x]` yasak; en azından
>   faz adı veya PR/commit referansı eklenir. "Ne zaman, hangi commit'le
>   kapandı?" sorusu altı ay sonra cevaplanabilmeli.
> - **Tamamlanmayan madde silmek yasak.** `[ ]` olarak kalır, yanına
>   **neden açık olduğunu** kısa bir cümleyle yaz. "Düşük öncelik",
>   "production gerekirse", "alternatif tasarım tercih edildi" gibi
>   gerekçe şart.
> - **PR sırasında open items güncelleme kontrolü atlanmaz.** Her
>   `make check` öncesi ya da commit hazırlanırken AI asistan ilgili
>   ADR'a bakıp güncelleme yapar. CLAUDE.md bu refleksi kurallaştırır.
> - **Open items'a yeni madde eklemek yasak değildir** — yeni gereksinim
>   çıkarsa kayda geçer. Ancak yeni madde eklerken **mevcut kapatılmış
>   maddeleri sterilize etmek yasak** (hâlâ referansları kalmalı).
> - **Madde silme yalnızca ADR superseded olduğunda mümkündür.** Aktif
>   ADR'da silme, geçmişi kaybetmektir.

## Context

11 ADR'da toplam **113 open item** vardı. 9 faz boyunca büyük çoğunluğu
(94 madde) tamamlandı ama **hiçbiri ADR'a geri dönüp işaretlenmedi**.
Sonuç:

- ADR'lar yanıltıcı bir görüntü veriyordu: "bu proje yarım kalmış" gibi
  duruyordu.
- Hangi madenin hangi PR'da kapandığını kimse bilmiyordu — sadece commit
  history'sini eşleştirerek bulmak mümkündü.
- Disiplin gevşemesi: ADR-0011 TDD refactor adımını zorunlu kıldı ama
  "open items refleksi" yazılı değildi.

Bu boşluğu **yazılı kural** olmaksızın kapamak imkansızdı. Bir kez yapılan
toparlamadan sonra (F12.1: 113 → 94 kapalı + 23 gerekçeli açık),
**tekrar etmemesi için sistemik kural** lazımdı.

Mevcut durum:

- `docs/decisions/0000-template.md` "Open items kapandıkça **silinir**"
  diyordu — ama bu pratikte kaybedilen tarihsel kayıt anlamına geliyordu.
- AI asistan (Claude Code) her faz sonunda commit + push yapıp bir
  sonraki faza geçiyordu; ADR'a dokunma refleksi yoktu.
- CLAUDE.md'de "Mandatory Approaches" altında Clean Code, TDD, Python
  Patterns, API Design vardı ama **ADR yaşam döngüsü** yoktu.

Kısıtlar:

1. **Hackathon ölçeği** — yeni süreç koymak hızı yavaşlatmamalı.
2. **AI uyumu** — kural CLAUDE.md'de yazılı olmalı ki Claude Code
   refleks haline getirsin.
3. **Geçmiş izlenebilirliği** — kapalı maddelerin nereye, ne zaman
   kapandığı görülebilmeli.

## Decision

### 1. Open items yaşam döngüsü

Üç durum:

- **`[ ] madde`** — henüz yapılmamış, **bilinçli olarak ertelenmiş**
  (gerekçe satır altında).
- **`[x] madde *(referans)*`** — tamamlanmış, kapatıldığı faz/PR/commit
  referansıyla.
- _silinmiş_ — yalnızca ADR superseded olduğunda.

### 2. Referans formatı

`[x] Madde adı. *(Fxx, PR #N — kısa açıklama)*`

Örnekler:

- `[x] pyproject.toml yaz. *(F1.2, PR #4)*`
- `[x] `engine.py`. *(F4.1 — WAL + foreign_keys pragma listener)*`
- `[x] README'de iki sağlayıcı hikayesi. *(F10 README rewrite,
  commit 7527624)*`

Referans en az **faz adı** veya **PR/commit** içermeli. Çıplak `[x]`
yasak.

### 3. Açık kalan maddenin gerekçesi

Tamamlanmamış maddenin yanına italic bir not:

- `[ ] Madde adı. *(Gerekçe: düşük öncelik, production gerekirse)*`
- `[ ] Madde adı. *(Mevcut çözüm bunu doğal karşılıyor — alternatif
  tasarım)*`
- `[ ] Madde adı. *(Stretch goal, hackathon kapsamı dışı)*`

Gerekçe **hayır**:
- "Daha sonra yapılacak"
- "TODO"
- Hiçbir şey yazmamak

Gerekçe **evet**:
- Spesifik bir teknik açıklama
- Önceliklendirme nedeni
- Alternatif tasarım kararının atfı

### 4. PR akışında ADR güncelleme

Her PR kapanmadan önce AI asistan (veya geliştirici) şu adımları izler:

1. PR'da değiştirilen dosyaları belirle (`git diff --name-only`).
2. Hangi ADR'ların "Affected areas" bu dosyaları içeriyor? — onların
   open items'ı tara.
3. Yeni tamamlanan maddeleri `[x] *(Fxx, PR #N)*` formatıyla işaretle.
4. Yeni ortaya çıkan iş varsa `[ ] *(gerekçe)*` olarak ekle.
5. `make check` çalıştır (ADR değişikliği test gerektirmez ama refleks
   refleksin).
6. ADR güncellemeleri commit'e dahil olur (`docs(adr):` veya
   ilgili katman prefix'iyle).

### 5. Template güncellemesi

`docs/decisions/0000-template.md` `## Open items` bölümü güncellenir:

> Henüz uygulanmamış veya tamamlandığında referansla işaretlenmiş
> maddeler. Format:
>
> - `[x] Madde. *(Fxx, PR #N — kısa açıklama)*` — tamamlandı, referans şart.
> - `[ ] Madde. *(Gerekçe: neden açık)*` — açık, gerekçe şart.
>
> **Silme yalnızca ADR superseded olduğunda.** Aktif ADR'da `[ ]` ve `[x]`
> birbirinin yanında yaşar; geçmiş kaybedilmez (ADR-0012).

### 6. CLAUDE.md entegrasyonu

`### 5. ADR (Architecture Decision Records)` bölümü genişletilir; mevcut
adr-kit kurulum talimatına ek olarak şu satır eklenir:

> **PR yaşam döngüsü:** Her PR kapanmadan önce ilgili ADR'ların open
> items'ı güncellenir. Tamamlanan maddeler `[x] *(referans)*` formatıyla
> işaretlenir; açık kalan maddeler gerekçeyle birlikte `[ ]` kalır.
> Detay: [ADR-0012](docs/decisions/0012-adr-yasam-dongusu-disiplini.md).

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **Kapatılan maddeyi sil (mevcut template kuralı)** | Geçmiş kaybedilir; "ne zaman, hangi PR'da kapandı?" sorusu cevapsız kalır. F12.1'de bu eksiklik somut bir bedele döndü. |
| **Sadece CLAUDE.md'ye satır ekle, ADR yazma** | Karar bağlayıcı olmaz; "neden böyle?" sorusu sözlü kalır. ADR yazılı olunca yeni geliştirici de okur. |
| **GitHub Action ile otomatik kontrol (PR'da değişen dosya → ADR güncellemesi var mı?)** | Hackathon ölçeğinde aşırı yatırım; pre-commit hook ya da CI check yazmak ek bakım. Manual disiplin + AI asistan refleksi yeterli. |
| **ADR yerine ayrı "implementation-log.md"** | Implementation ile kararı ayırmak güzel görünür ama ADR'ın "Affected areas + Open items" bölümleri zaten bu işi yapacak şekilde tasarlanmış. Yeni dosya türü gereksiz parçalanma. |
| **Open items'ı topluca docs/concepts/'e taşı** | ADR'ın self-contained olma özelliği bozulur; "bu kararı bilmek için 3 ayrı dosyaya bakmalısın" durumu. |

## Consequences

### Olumlu

- **ADR'lar gerçeği yansıtır:** Sunum/jüri/yeni geliştirici ADR'a baktığında
  "tamamlanmış" ve "bilinçli açık" maddeleri ayırt eder.
- **Tarihsel izlenebilirlik:** Hangi maddenin hangi PR'da kapandığı tek
  ADR'da görülür; commit history'sini eşleştirmek gereksizdir.
- **Disiplin sözlü değil yazılı:** AI asistan ve insan geliştirici aynı
  kuralı takip eder; CLAUDE.md bağlayıcıdır.
- **Açık kalan iş borç olarak görünür:** Her açık `[ ]` gerekçeli olduğu
  için "bilinçli teknik borç" haline gelir; gizli kalmaz.

### Olumsuz

- **PR sırasında ek adım:** Her PR'da ADR güncelleme gözden geçirmesi
  yapılır. Pratikte 30 saniye; ama bilinçli olarak yapılmalı.
- **Format disiplini:** Referans formatı `(Fxx, PR #N — açıklama)`
  unutulabilir; AI asistan refleks haline gelene kadar küçük sürtünme.
- **ADR superseded edildiğinde geçmiş silinir:** Bu ADR'ın belirttiği
  istisna — yeni ADR'a geçişte kayıt kaybı olur. Karşılığı: yeni ADR
  "Supersedes: ADR-XXXX" referansını taşır, eski ADR git history'sinden
  hep okunabilir.

## Open items

- [x] Mevcut 11 ADR'da open items'ı koda göre işaretle. *(F12.1; 94 kapatıldı, 23 gerekçeli açık)*
- [x] `docs/decisions/0000-template.md` Open items bölümünü güncelle. *(bu ADR ile birlikte)*
- [x] `CLAUDE.md` `### 5. ADR` bölümüne PR yaşam döngüsü satırı. *(bu ADR ile birlikte)*
- [x] `docs/index.md`'ye ADR-0012 satırı. *(bu ADR ile birlikte)*
- [ ] **İlk PR'da AI asistanın bu refleksi uyguladığını doğrula.** *(F12 sonrası ilk yeni feature PR'ı; gerçek refleks testi)*

## Affected areas

- `docs/decisions/0000-template.md` — Open items bölümü güncellenecek
- `docs/decisions/00*.md` — tüm mevcut ADR'lar bu disiplini takip eder
- `CLAUDE.md` — `### 5. ADR` bölümü genişler
- `docs/index.md` — ADR listesine satır
- [[0011-tdd-refactor-disiplini]] — bu ADR ile aynı kategoride
  (yazılı disiplin, AI asistan refleksi)
