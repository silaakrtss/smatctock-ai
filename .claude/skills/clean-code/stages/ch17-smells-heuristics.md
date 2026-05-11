# Chapter 17: Smells and Heuristics

> "A code smell is a surface indication that usually corresponds to a deeper problem in the system." — Robert C. Martin

## Özet

Bu bölüm Clean Code kitabının referans kataloğudur. Tüm code smell'ler ve sezgisel kurallar (heuristics) kategorize edilmiştir. Kod yazarken veya review yaparken bu listeyi kontrol listesi olarak kullan.

## C: Comments (Yorum Kokuları)

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **C1** | Inappropriate Information | Değişiklik geçmişi, yazar bilgisi gibi başka sistemlerde tutulması gereken bilgiler |
| **C2** | Obsolete Comment | Güncelliğini yitirmiş, artık doğru olmayan yorumlar |
| **C3** | Redundant Comment | Kodun zaten söylediğini tekrarlayan yorumlar: `i++; // increment i` |
| **C4** | Poorly Written Comment | Yazılacaksa iyi yazılmalı — kısa, öz, dilbilgisi doğru |
| **C5** | Commented-Out Code | Yorum satırına alınmış kod. Sil! Versiyon kontrol sistemi hatırlar |

**AI Agent Kuralı:** Yorum yazmadan önce → kodu daha açık yazabilir misin? Evet → yorumu yazma.

## E: Environment (Ortam Kokuları)

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **E1** | Build Requires More Than One Step | Derleme tek komutla yapılabilmeli |
| **E2** | Tests Require More Than One Step | Tüm testler tek komutla çalışabilmeli |

**AI Agent Kuralı:** Build ve test komutları basit ve tek adım olmalı.

## F: Functions (Fonksiyon Kokuları)

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **F1** | Too Many Arguments | 3'ten fazla parametre → Parameter Object kullan |
| **F2** | Output Arguments | Çıktı parametresi kafa karıştırır → return kullan |
| **F3** | Flag Arguments | Boolean parametre → fonksiyonu ikiye böl |
| **F4** | Dead Function | Hiç çağrılmayan fonksiyon → sil |

## G: General (Genel Kokular)

### Çoklu Dil ve Tekrar

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **G1** | Multiple Languages in One Source File | Bir dosyada birden fazla dil karıştırma |
| **G2** | Obvious Behavior Is Unimplemented | Beklenen davranış eksik → sürpriz yaratır |
| **G3** | Incorrect Behavior at the Boundaries | Sınır koşulları test edilmemiş |
| **G4** | Overridden Safeties | Uyarıları, hataları susturma, güvenlik kontrollerini devre dışı bırakma |
| **G5** | Duplication | HER TÜRLÜ tekrar. DRY'ın en büyük düşmanı |

### Soyutlama ve Tasarım

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **G6** | Code at Wrong Level of Abstraction | Yüksek seviye sınıfta düşük seviye detay |
| **G7** | Base Classes Depending on Derivatives | Üst sınıf, alt sınıfı bilmemeli |
| **G8** | Too Much Information | Arayüzde çok fazla metot/alan → dar ve derin ol |
| **G9** | Dead Code | Ulaşılamayan kod → sil |
| **G10** | Vertical Separation | Tanım ve kullanım birbirinden uzak |

### Tutarsızlık ve Karmaşıklık

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **G11** | Inconsistency | Bir yerde `processVerb()` diğerinde `handleVerb()` → tutarlı ol |
| **G12** | Clutter | Kullanılmayan değişken, boş constructor, gereksiz yorum → sil |
| **G13** | Artificial Coupling | İlgisiz kavramlar arasında gereksiz bağımlılık |
| **G14** | Feature Envy | Metot kendi sınıfından çok başka sınıfın verisiyle çalışıyor → taşı |
| **G15** | Selector Arguments | Boolean/enum parametre davranış seçiyor → polimorfizm kullan |
| **G16** | Obscured Intent | Kısa ama anlaşılmaz kod (tek harfli değişkenler, sihirli sayılar) |
| **G17** | Misplaced Responsibility | Fonksiyon yanlış sınıfta → en çok bilgiyi bilen sınıfa taşı |

### Statik ve Dinamik

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **G18** | Inappropriate Static | Polimorfizm gerekebilecek metotları static yapma |
| **G19** | Use Explanatory Variables | Karmaşık ifadeleri açıklayıcı ara değişkenlere böl |
| **G20** | Function Names Should Say What They Do | İsim yetmiyorsa fonksiyon çok karmaşık |
| **G21** | Understand the Algorithm | Kodu "çalışıyor" diye bırakma, neden çalıştığını anla |
| **G22** | Make Logical Dependencies Physical | Mantıksal bağımlılığı kodda açıkça ifade et |

### Polimorfizm ve Koşullar

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **G23** | Prefer Polymorphism to If/Else | if/else zinciri → Strategy/Visitor pattern |
| **G24** | Follow Standard Conventions | Takım kurallarına uy |
| **G25** | Replace Magic Numbers with Named Constants | `86400` → `SECONDS_PER_DAY` |
| **G26** | Be Precise | Belirsizlik kodda kabul edilemez. Float vs Decimal, List vs Set |

### Yapı ve Kapsülleme

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **G27** | Structure Over Convention | Kural yerine yapıyla zorla (interface > yorum) |
| **G28** | Encapsulate Conditionals | `if (shouldBeDeleted(timer))` > `if (timer.hasExpired() && !timer.isRecurrent())` |
| **G29** | Avoid Negative Conditionals | `if (buffer.shouldCompact())` > `if (!buffer.shouldNotCompact())` |
| **G30** | Functions Should Do One Thing | Bir fonksiyon = bir soyutlama seviyesi |

### Bağımlılık ve Sihirli Sayılar

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **G31** | Hidden Temporal Couplings | Fonksiyon çağrı sırası önemliyse → bunu yapıda ifade et |
| **G32** | Don't Be Arbitrary | Kod yapısında keyfi kararlar verme, her seçimin nedeni olsun |
| **G33** | Encapsulate Boundary Conditions | `level + 1` gibi sınır koşullarını değişkene ata: `nextLevel = level + 1` |
| **G34** | Functions Should Descend One Level of Abstraction | Fonksiyon içinde tek soyutlama seviyesi |
| **G35** | Keep Configurable Data at High Levels | Sabitler, eşik değerleri üst seviyede tanımlan |
| **G36** | Avoid Transitive Navigation | Law of Demeter: `a.getB().getC()` → `a.getC()` delegate et |

## J: Java-Specific (Java Kokuları)

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **J1** | Avoid Long Import Lists by Using Wildcards | Uzun import listeleri → wildcard kullan (tartışmalı) |
| **J2** | Don't Inherit Constants | Sabitlere erişmek için interface'ten miras alma → static import |
| **J3** | Constants vs Enums | `public static final int` → `enum` kullan |

**Not:** J1 modern araçlarda tartışmalıdır. Birçok stil rehberi wildcard import'u yasaklar.

## N: Names (İsimlendirme Kokuları)

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **N1** | Choose Descriptive Names | İsim seçmek için zaman harca, sonra değiştir |
| **N2** | Choose Names at the Appropriate Level of Abstraction | Uygulama detayını değil, soyutlamayı isimlendirme |
| **N3** | Use Standard Nomenclature Where Possible | Design pattern isimleri: Factory, Strategy, Observer |
| **N4** | Unambiguous Names | Belirsizlik yok: `rename()` → `renameFile()` |
| **N5** | Use Long Names for Long Scopes | Kısa kapsam → kısa isim OK, geniş kapsam → uzun, açıklayıcı isim |
| **N6** | Avoid Encodings | Tür bilgisi isimlere gömme: `strName` → `name` |
| **N7** | Names Should Describe Side Effects | `getOos()` yerine `createOrReturnOos()` |

## T: Tests (Test Kokuları)

| Kod | Smell | Açıklama |
|-----|-------|----------|
| **T1** | Insufficient Tests | Yeterli test yok → her koşul, her sınır test edilmeli |
| **T2** | Use a Coverage Tool | Kapsam aracı kullan, köşeleri bul |
| **T3** | Don't Skip Trivial Tests | Basit testleri atlama → belgeleme değeri var |
| **T4** | An Ignored Test Is a Question About an Ambiguity | Devre dışı test = belirsizlik sorusu |
| **T5** | Test Boundary Conditions | Sınır koşullarını mutlaka test et |
| **T6** | Exhaustively Test Near Bugs | Hata bulunan yerde daha fazla hata vardır |
| **T7** | Patterns of Failure Are Revealing | Hangi testler başarısız → pattern'i oku |
| **T8** | Test Coverage Patterns Can Be Revealing | Kapsanmayan kodun pattern'i sorun gösterir |
| **T9** | Tests Should Be Fast | Yavaş testler çalıştırılmaz → çalıştırılmayan test değersizdir |

## Hızlı Referans: Kategoriye Göre Sayılar

| Kategori | Sayı | Kapsam |
|----------|------|--------|
| Comments (C) | 5 | C1-C5 |
| Environment (E) | 2 | E1-E2 |
| Functions (F) | 4 | F1-F4 |
| General (G) | 36 | G1-G36 |
| Java (J) | 3 | J1-J3 |
| Names (N) | 7 | N1-N7 |
| Tests (T) | 9 | T1-T9 |
| **TOPLAM** | **66** | |

## AI Agent İçin Kontrol Listesi

### Kod Yazarken
- [ ] Tekrar var mı? (G5 - DRY)
- [ ] Sihirli sayı var mı? (G25)
- [ ] Fonksiyon birden fazla şey yapıyor mu? (G30)
- [ ] if/else zinciri var mı? (G23 → polimorfizm)
- [ ] Train wreck var mı? (G36 → Law of Demeter)
- [ ] Negatif koşul var mı? (G29)
- [ ] İsimler niyet ifade ediyor mu? (N1, N4)
- [ ] Ölü kod var mı? (G9, F4)

### Review Yaparken
- [ ] Yorum gerçekten gerekli mi? (C1-C5)
- [ ] Fonksiyon parametresi 3'ten fazla mı? (F1)
- [ ] Boolean parametre var mı? (F3)
- [ ] Sınır koşulları test edilmiş mi? (G3, T5)
- [ ] Build/test tek adımda çalışıyor mu? (E1, E2)
- [ ] Testler yeterli ve hızlı mı? (T1, T9)
