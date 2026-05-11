# TDD Refactor Checklist

Red-Green-**Refactor** döngüsünün en çok unutulan adımı **Refactor**'dür.
Test yeşil olunca beyin "bitti" der; oysa tasarım kararlarının yarısı bu
adımda alınır. Bu sayfa "yeşil testin üstünde durup neye bakacağım"
sorusunun pratik cevabıdır.

> **Altın kural:** *When you refactor, don't change behavior. When you
> change behavior, don't refactor.* — Kent Beck
>
> Refactor SADECE yeşil testlerle yapılır. Test kırılırsa sorun 5 saniye
> önce yazdığın satırdadır.

İlgili skill'ler: `tdd-workflow`, `clean-code`, `coding-standards`,
`python-patterns`.

---

## 1. Duplikasyon (DRY)

- [ ] Birebir aynı kod iki+ yerde mi? → **Extract Method/Function**.
- [ ] Benzer ama tam aynı değil mi? → Önce birebir aynı hale getir,
      sonra çıkar.
- [ ] Sadece kod değil; **bilgi duplikasyonu** da bak (aynı magic
      number, aynı string literal, aynı iş kuralı iki yerde).

## 2. İsimlendirme

- [ ] Geçici/anlamsız isimler kaldı mı? (`tmp`, `data`, `result`, `helper`)
- [ ] İsim niyeti açıklıyor mu? (`d` → `elapsedDays`)
- [ ] Boolean'lar soru formatında mı? (`isActive`, `hasPermission`,
      `canExecute`)
- [ ] Yanlış bilgi veriyor mu? (`accountList` ama tip `set`)
- [ ] Süreç: *nonsense → vague → precise → meaningful*.

## 3. Fonksiyon / Metot Boyutu

- [ ] 20 satırı aşan fonksiyon var mı? (Global Clean Code limiti)
- [ ] Tek bir şey mi yapıyor? (SRP)
- [ ] **Composed Method**: kod gazete makalesi gibi okunmalı —
      üstte high-level akış, altta detaylar.
- [ ] Parametre sayısı 3'ü aştı mı? → Parametre objesi (dataclass /
      Pydantic model).
- [ ] Sınıf 200 satırı aştı mı? → SRP ihlali kokusu.

## 4. Code Smell'ler

- [ ] **Magic number / string** → named constant.
- [ ] **Long parameter list** → object / builder.
- [ ] **Feature envy**: bir metot başka sınıfın verisini sürekli
      soruyorsa, yanlış sınıfta olabilir.
- [ ] **Shotgun surgery**: tek değişiklik 5 sınıfa yayılıyorsa,
      sorumluluk yanlış dağıtılmış.
- [ ] **Solution sprawl**: basit iş için 5 sınıf gerekiyorsa basitleştir.
- [ ] **Train wreck** `a.b().c().d().e()` → Law of Demeter ihlali.
- [ ] **Flag argument** `doSomething(flag=True)` → iki ayrı fonksiyon.
- [ ] **Primitive obsession**: `str`, `int` her yerde → value object.

## 5. Test Kalitesi (refactor SADECE üretim kodu değildir!)

- [ ] Test adı davranışı anlatıyor mu?
      (`test_calculates_total` değil `test_returns_zero_for_empty_cart`)
- [ ] Test içinde **birden fazla Arrange-Act-Assert** döngüsü var mı?
      → Böl.
- [ ] **Arrange bölümü çok uzunsa** → tasarım kokusu (çok bağımlılık,
      yapıcı parametresi şişmiş).
- [ ] Test **implementation detail** mı, **input/output** mu doğruluyor?
- [ ] Magic value'lar testlerde de açıklayıcı isim almalı.
- [ ] Setup/fixture duplikasyonu → ortak fixture / helper.
- [ ] FIRST prensibi: **F**ast, **I**ndependent, **R**epeatable,
      **S**elf-validating, **T**imely.

## 6. Hata Yönetimi

- [ ] `None` dönüyor mu? → `Optional` tipini açıkça belirt veya
      Result/empty-collection döndür.
- [ ] Genel `except Exception` var mı? → Spesifik exception.
- [ ] Yutulmuş exception var mı? → log veya rethrow.
- [ ] Hata uygun katmanda mı yakalanıyor? (domain'de değil application
      veya presentation'da)

## 7. Yorumlar

- [ ] WHAT yorumu yazılmış mı? → koda taşı veya sil.
- [ ] Commented-out kod var mı? → sil (VCS hatırlar).
- [ ] Sadece şunlar kalsın: WHY, legal, sonuç uyarısı, ticket'lı TODO.

## 8. Tasarım / Mimari Sinyaller

- [ ] **Cyclomatic complexity** arttı mı? (iç içe if/for derinleşti mi)
- [ ] Cohesion düşük mü? (alakasız metotlar tek sınıfta)
- [ ] Coupling yüksek mi? (her şey her şeyi import ediyor)
- [ ] ADR ihlali var mı? (örn. domain'den infra'ya import, port
      tanımsız adapter)

## 9. Refactor Disiplini

- [ ] **Tek seferde tek tip değişiklik** — davranış değişikliği ile
      refactor karışmasın (ayrı commit'ler).
- [ ] **Küçük adımlar** — her adım sonrası testler hâlâ yeşil mi?
- [ ] Refactor için yeni test yazmadın değil mi? (Refactor mevcut
      testleri kullanır; yeni davranış yeni Red ister.)
- [ ] Commit mesajı `refactor:` öneki ile mi başlıyor?

---

## Hızlı Tarama (PR review için 30 saniyelik versiyon)

1. **Duplikasyon var mı?**
2. **Her isim niyetini söylüyor mu?**
3. **Hiçbir fonksiyon 20 satırı geçmiyor mu?**
4. **Magic number / flag arg / null return yok mu?**
5. **Test adı davranışı anlatıyor mu?**

Beşi de "evet" ise refactor adımı tamamlanmıştır.

---

## Kaynaklar

- [TDD MOOC — Chapter 2: Refactoring and design](https://tdd.mooc.fi/2-design/)
- [Martin Fowler — Test Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Mark Seemann — A red-green-refactor checklist](https://blog.ploeh.dk/2019/10/21/a-red-green-refactor-checklist/)
- [Agile in a Flash — TDD Process Smells](http://agileinaflash.blogspot.com/2009/03/tdd-process-smells.html)
- [Red, green, and don't forget refactor — mokacoding](https://mokacoding.com/blog/red-green-and-dont-forget-refactor/)
