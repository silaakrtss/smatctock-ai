# ADR 0011: tdd-refactor-disiplini

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** TDD döngüsünün **Refactor** adımı her değişiklikte zorunlu
> bir kapıdır; "yeşil test → commit" doğrudan akışı yasaktır. Refactor
> kapsamı kodlanmış bir **checklist** ile sabitlenir; checklist
> `docs/concepts/tdd-refactor-checklist.md` altında yaşar ve
> güncellenebilir. CLAUDE.md `### 2. TDD` bölümü bu checklist'e link verir.
> AI asistan (Claude Code) bir TDD turu kapatmadan önce checklist'in
> hızlı tarama (5 madde) versiyonunu mental olarak geçer.
>
> **Kapsam:** Tüm üretim kodu değişiklikleri (domain, application,
> infrastructure, presentation). Test dosyaları da refactor kapsamındadır
> — checklist test kalitesi maddelerini içerir.
>
> **Önemli kısıtlar:**
> - **"Yeşil → commit" yasak.** Refactor adımı atlanamaz; en azından
>   hızlı tarama (5 madde) yapılır.
> - **Refactor ile davranış değişikliği aynı commit'te birleştirilemez.**
>   Ayrı commit'ler: `feat:` / `fix:` davranış, `refactor:` davranışsız.
> - **Refactor için yeni test yazılmaz.** Yeni davranış istiyorsan yeni
>   Red turu başlat.
> - **Test dosyaları refactor edilir** — duplike fixture, uzun arrange,
>   muğlak test adı kod kokusudur.
> - Checklist `concepts/` altında **yaşayan dokümandır**; madde eklemek
>   için yeni ADR gerekmez, sadece güncelle.

## Context

TDD `red-green-refactor` döngüsünün üçüncü adımı pratikte en sık atlanan
adımdır. Sebepler:

- Test yeşil olunca beyin "bitti" sinyali verir; refactor bilişsel olarak
  ek iş gibi hisseder.
- "Bir dahaki turda temizlerim" ertelemesi → asla temizlenmeyen kod.
- "Hangi açıdan bakacağım" belirsizliği → karar yorgunluğu → atlama.
- AI asistan (Claude) yeşil testten sonra doğrudan commit önerirse
  disiplin çöker.

Mevcut durum:

- CLAUDE.md `### 2. TDD` bölümü TODO; refactor disiplini yazılı değil.
- `tdd-workflow` skill'i red-green-refactor'ü adlandırıyor ama proje
  bağlamına özel checklist sağlamıyor.
- `clean-code` skill'i ve global `~/.claude/rules/clean-code.md` Clean
  Code limitleri (20 satır, 200 satır, 3 parametre) zaten var; refactor
  adımı bu limitleri **uygulamak için doğal zaman**.
- ADR-0002 katmanlı mimari + ADR-0003 test stack zaten kabul edilmiş;
  refactor checklist bu kararların **günlük disiplin yüzeyidir**.

Kısıtlar:

1. **Düşük sürtünme** — checklist 9 başlık + ~40 madde; PR review için
   30 saniyelik "hızlı tarama" versiyonu zorunlu.
2. **Güncellenebilir** — yeni kod kokusu öğrendikçe ekleyebilmeliyiz;
   bu yüzden ADR (immutable) değil, `concepts/` (yaşayan) içine yazılır.
3. **AI asistan dostu** — Claude Code yeşil testten sonra checklist'i
   refleks olarak geçmeli; CLAUDE.md `### 2. TDD` bölümü bu davranışı
   tetiklemeli.
4. **Mevcut skill'lerle çakışmasın** — `clean-code` ve `tdd-workflow`
   genel rehber; bu checklist proje bazında **refactor anında neye
   bakacağım** odaklı pratik liste.

## Decision

1. **Refactor adımı zorunlu kapıdır.** Yeşil test + checklist taraması
   olmadan commit'lenmez. AI asistan da bu sıraya uyar.
2. **Checklist konumu:** `docs/concepts/tdd-refactor-checklist.md`.
   Yaşayan doküman; madde eklemek için yeni ADR açılmaz.
3. **Checklist iki ölçekte yazılır:**
   - **Tam liste** (9 başlık × ~40 madde) — bilinçli refactor seansı için.
   - **Hızlı tarama** (5 madde) — her PR / her tur için 30 saniye.
4. **CLAUDE.md `### 2. TDD` bölümü** kısa özet + checklist linki içerir;
   detay tekrar yazılmaz (single source of truth).
5. **Test dosyaları refactor kapsamındadır.** Checklist "Test Kalitesi"
   başlığı (madde 5) test kodu için.
6. **Commit ayrımı zorunlu:** davranış değiştiren commit `feat:` / `fix:`,
   davranışsız temizlik `refactor:`. Aynı commit'te birleştirilmez
   (cf. `feedback_git_commits.md`).
7. **Refactor için yeni test yazılmaz.** Yeni davranış için yeni Red turu.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| Checklist'i CLAUDE.md'ye gömmek | CLAUDE.md hızla şişer; ADR ve concept ayrımı yiter. Tek satırda link daha temiz. |
| Checklist'i ADR'a (immutable) gömmek | Yeni kod kokusu öğrendikçe güncellemek için her seferinde yeni ADR açmak gerekir; refactor disiplini ise yaşayan bir şey. |
| Sadece `tdd-workflow` skill'ine güvenmek | Skill genel; proje bazında **bu projede neye bakıyoruz** disiplinini sağlamaz. Ayrıca skill `concepts/` ile çakışmaz; tamamlayıcıdır. |
| Pre-commit hook ile linter'a bırakmak | Linter syntactic (line length, unused import) yakalar; "feature envy", "primitive obsession", "test adı niyeti söylüyor mu" gibi semantik kokuları yakalayamaz. İnsan + checklist gerekli. |
| Hiç checklist tutmamak, "Clean Code'u uygula" demek | Çok soyut; karar yorgunluğunda atlanır. Somut madde listesi disiplini sürdürür. |
| Sadece "hızlı tarama" (5 madde) tutmak | Bilinçli refactor seansı için fazla yüzeysel; derin temizlik gerektiğinde tam liste lazım. İki ölçek birlikte. |

## Consequences

### Olumlu

- Refactor adımı atlanmaz hale gelir; teknik borç birikimi yavaşlar.
- Checklist güncellenebilir → ekip yeni kokular öğrendikçe disiplin gelişir.
- AI asistan (Claude) yeşil testten sonra refleks olarak checklist'i
  geçer; "yeşil → commit" tuzağı kapanır.
- Mevcut Clean Code limitleri (20/200/3) refactor anında **uygulanır**,
  sadece "kural olarak var" kalmaz.
- Test dosyaları da refactor kapsamına girer → testler fragile olmaktan
  çıkar.
- Commit ayrımı (`feat`/`fix` vs `refactor`) `git log`'u okunabilir kılar.

### Olumsuz

- Her tur için ek bilişsel maliyet (~30 sn hızlı tarama).
- Hızlı tarama yetmeyen durumlarda tam listeyi geçmek ekstra 2-5 dk.
- Checklist çok şişerse disiplin kaybedilir; **uzunluk denetimi** gerekir
  (Seemann'ın "checklist küçük olmalı" prensibi).
- Refactor commit'leri PR sayısını artırabilir; karşılığında diff okunaklı.

## Open items

- [x] `docs/concepts/tdd-refactor-checklist.md` oluştur.
- [x] CLAUDE.md `### 2. TDD` bölümünü güncelle (özet + link).
- [x] `docs/index.md` concepts tablosuna satır ekle.
- [ ] İlk birkaç PR'da pratik geri bildirimle checklist'i revize et
      (madde ekle/çıkar).
- [ ] Checklist 50 maddeyi geçerse Seemann kuralı gereği budama yap.

## Affected areas

- `docs/concepts/tdd-refactor-checklist.md` — yeni dosya, checklist.
- `docs/index.md` — concepts tablosuna satır.
- `CLAUDE.md` — `### 2. TDD` bölümü doldurulur, checklist'e link verir.
- `~/.claude/rules/clean-code.md` (global) — bu ADR onun limitlerini
  refactor anında **uygulama yüzeyi** olarak kullanır; çakışma yok.
- [[0002-mimari-yaklasim-layered-agent]] — refactor disiplini katman
  sınırlarını koruyan günlük yüzeydir.
- [[0003-cerceve-teknoloji-yigini]] — test stack (pytest) bu disiplinin
  ön koşulu.
