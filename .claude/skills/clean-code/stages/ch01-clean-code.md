# Chapter 1: Clean Code

> "The only way to go fast, is to go well." — Robert C. Martin

## Özet

Temiz kod, yalnızca çalışır durumda olan kod değil; okunabilir, anlaşılabilir ve değiştirilebilir olan koddur. Robert C. Martin bu bölümde kötü kodu yığmanın maliyetini, ustaların temiz kod tanımlarını ve Boy Scout Rule'u anlatır. Ana mesaj: kod yazmaktan çok okunur; bu yüzden okunabilirlik için optimize edilmelidir.

## Temel Prensipler

| Prensip | Açıklama | Kötü Örnek | İyi Örnek |
|---------|----------|------------|-----------|
| Okunabilirlik Öncelikli | Kod yazma/okuma oranı 1:10'dur | Kısaltmalar ve tek harfli değişkenlerle dolu kod | Niyet belirten isimler ve küçük fonksiyonlar |
| Boy Scout Rule | Kodu bulduğundan daha temiz bırak | "Sonra temizlerim" deyip dokunmamak | Her dokunuşta küçük bir iyileştirme yapmak |
| LeBlanc's Law | "Sonra" asla gelmez | `// TODO: refactor this later` (hiçbir zaman yapılmaz) | İlk seferde doğru yaz veya hemen temizle |
| Tek Sorumluluk | Her birim tek bir işi iyi yapmalı | `validateAndSaveAndNotify()` | `validate()`, `save()`, `notify()` ayrı ayrı |
| Açıklık | Kod sürpriz içermemeli | Gizli side-effect'ler | Fonksiyon adı tüm davranışı açıklar |

## Ustaların Temiz Kod Tanımları

### Bjarne Stroustrup (C++ Yaratıcısı)

> "I like my code to be elegant and efficient. The logic should be straightforward to make it hard for bugs to hide, the dependencies minimal to ease maintenance, error handling complete according to an articulated strategy, and performance close to optimal so as not to tempt people to make the code messy with unprincipled optimizations. Clean code does one thing well."

**Anahtar kavramlar:** Zarafet (elegance), düzgün mantık (straightforward logic), minimal bağımlılık, eksiksiz hata yönetimi, tek bir işi iyi yapmak.

### Grady Booch (UML'in Babası)

> "Clean code is simple and direct. Clean code reads like well-written prose. Clean code never obscures the designer's intent but rather is full of crisp abstractions and straightforward lines of control."

**Anahtar kavramlar:** Basitlik, iyi yazılmış nesir gibi okunma, tasarımcının niyetini gizlememek, net soyutlamalar (crisp abstractions).

### Dave Thomas (OTI Kurucu Ortağı)

> "Clean code can be read, and enhanced by a developer other than its original author. It has unit and acceptance tests. It has meaningful names. It provides one way rather than many ways for doing one thing. It has minimal dependencies, which are explicitly defined, and provides a clear and minimal API."

**Anahtar kavramlar:** Başkası tarafından okunabilir ve geliştirilebilir, testleri var, anlamlı isimler, minimal ve açık bağımlılıklar.

### Michael Feathers

> "Clean code always looks like it was written by someone who cares. There is nothing obvious that you can do to make it better."

**Anahtar kavram:** Özen (care). Temiz kod, yazarının özen gösterdiğini hissettirir.

### Ron Jeffries (Extreme Programming Öncüsü)

Ron Jeffries temiz kodu dört kural ile tanımlar (öncelik sırasına göre):

1. **Tüm testleri geçer** (Runs all the tests)
2. **Tekrar içermez** (Contains no duplication)
3. **Sistemdeki tüm tasarım fikirlerini ifade eder** (Expresses all the design ideas)
4. **Sınıf, metot, fonksiyon gibi varlıkların sayısını minimize eder** (Minimizes entities)

### Ward Cunningham (Wiki ve XP Mucidi)

> "You know you are working on clean code when each routine you read turns out to be pretty much what you expected. You can call it beautiful code when the code also makes it look like the language was made for the problem."

**Anahtar kavram:** Beklentiye uygunluk (no surprises). Bir fonksiyonu okuduğunuzda "evet, tam da bunu bekliyordum" diyorsanız, temiz koddaysınız.

## Kurallar

### Kural 1: The Total Cost of Owning a Mess

Kötü kod zaman içinde birikerek üretkenliğe olan etkisini artırır. İlk başta hızlı ilerlersiniz ama dağınıklık biriktikçe her değişiklik daha uzun sürer. Sonunda takım "sıfırdan yazalım" der — ki bu da genellikle başarısız olur çünkü aynı hatalar tekrarlanır.

### Kural 2: LeBlanc's Law — Later Equals Never

"Sonra temizlerim" = "asla temizlemem". Kod ilk yazıldığında temiz olmalıdır.

### Kural 3: Boy Scout Rule

> "Leave the campground cleaner than you found it." — Boy Scouts of America

Her commit'te, her dosyaya dokunduğunuzda küçük bir iyileştirme yapın:

```
// Bir fonksiyonda bug fix'lerken gördünüz:
int d; // elapsed time in days

// Geçtikten sonra bırakmayın, değiştirin:
int elapsedTimeInDays;
```

### Kural 4: Reading vs. Writing Ratio (10:1)

Kod okuma/yazma oranı 10:1'den fazladır. Daha uzun yazılmış ama okunması kolay kod, kısa ama gizemli koddan her zaman üstündür.

## Temiz Kod Formülü

```
Temiz Kod =
    Okunabilir    (herkes anlayabilir)
  + Basit         (gereksiz karmaşıklık yok)
  + Bakılabilir   (değişiklik yapmak kolay)
  + Test edilmiş  (güvenle değiştirilebilir)
  + Özenli        (yazarın umursadığını hissettirir)
  + Sürprizsiz    (beklediğinizi bulursunuz)
```

## Anti-Pattern'ler

| Anti-Pattern | Neden Kötü | Çözüm |
|--------------|------------|-------|
| "Çalışıyor, dokunma" zihniyeti | Kod çürüyor, her değişiklik daha zor | Boy Scout Rule uygula |
| "Sonra temizlerim" sözü | LeBlanc Yasası: Sonra asla gelmez | İlk seferde temiz yaz |
| Büyük Yeniden Yazım | Aylar/yıllar sürer, eski hataları tekrarlar | Sürekli küçük iyileştirmeler yap |
| Hız için kaliteden ödün verme | Kısa vadede hızlı, uzun vadede felaket | "Tek hızlı yol, iyi yapmaktır" |

## AI Agent İçin Kontrol Listesi

- [ ] Kod, yazarından başka biri tarafından anlaşılabilir mi?
- [ ] Her fonksiyon tek bir iş yapıyor mu?
- [ ] Değişken ve fonksiyon isimleri niyeti açıklıyor mu?
- [ ] "Sonra temizlerim" diye bırakılan bir yer var mı? (varsa şimdi temizle)
- [ ] Mevcut koda dokunduysan, daha temiz bıraktın mı? (Boy Scout Rule)
- [ ] Kod sürpriz içeriyor mu? (Fonksiyon adı söylemediği bir şey yapıyor mu?)
- [ ] Gereksiz karmaşıklık var mı? (YAGNI — ihtiyaç olmayan şeyi yazma)
