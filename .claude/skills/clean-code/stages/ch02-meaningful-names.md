# Chapter 2: Meaningful Names

> "The name of a variable, function, or class, should answer all the big questions. It should tell you why it exists, what it does, and how it is used." — Robert C. Martin

## Özet

İsimlendirme yazılımın en temel ve en zor becerilerinden biridir. İyi isimler kodu self-documenting yapar, kötü isimler ise yorum gerektiren, yanıltıcı ve aranması imkansız bir kod ortamı oluşturur.

## Temel Prensipler

| Prensip | Açıklama | Kötü Örnek | İyi Örnek |
|---------|----------|------------|-----------|
| Intent-Revealing | İsim niyeti açıklamalı | `int d;` | `int elapsedTimeInDays;` |
| Avoid Disinformation | Yanıltıcı isimlerden kaçın | `accountList` (aslında Set) | `accounts` |
| Meaningful Distinctions | Fark anlamlı olmalı | `a1`, `a2`, `ProductInfo` vs `ProductData` | `source`, `destination` |
| Pronounceable | Telaffuz edilebilir olmalı | `genymdhms` | `generationTimestamp` |
| Searchable | Aranabilir olmalı | `7`, `e` | `MAX_CLASSES_PER_STUDENT` |
| No Encodings | Tür bilgisi isme konmamalı | `strName`, `iCount` | `name`, `count` |

## Kurallar

### Kural 1: Use Intention-Revealing Names

Bir isim şu soruları yanıtlamalı: Neden var? Ne yapar? Nasıl kullanılır?

```
// KÖTÜ: İsim hiçbir şey anlatmıyor
int d; // elapsed time in days

// İYİ: İsim her şeyi anlatıyor
int elapsedTimeInDays;
```

```
// KÖTÜ
function getThem() {
    let list1 = [];
    for (let x of theList)
        if (x[0] === 4)
            list1.push(x);
    return list1;
}

// İYİ
function getFlaggedCells() {
    let flaggedCells = [];
    for (let cell of gameBoard)
        if (cell.isFlagged())
            flaggedCells.push(cell);
    return flaggedCells;
}
```

### Kural 2: Avoid Disinformation

```
// KÖTÜ: "List" diyor ama belki Set veya Map
accountList = getAccounts()   // Ama gerçekte bir HashSet dönüyor!

// İYİ
accounts = getAccounts()
```

### Kural 3: Make Meaningful Distinctions

```
// KÖTÜ: Sayı serisi
function copyChars(a1, a2) {
    for (let i = 0; i < a1.length; i++)
        a2[i] = a1[i];
}

// İYİ
function copyChars(source, destination) {
    for (let i = 0; i < source.length; i++)
        destination[i] = source[i];
}
```

Gürültü kelimeleri tuzağı: `Product`, `ProductInfo`, `ProductData` — Info ve Data hiçbir şey eklemiyor!

### Kural 4: Use Pronounceable Names

```
// KÖTÜ
class DtaRcrd102 {
    Date genymdhms;
}

// İYİ
class Customer {
    Date generationTimestamp;
}
```

### Kural 5: Use Searchable Names

İsmin uzunluğu, kapsam alanının (scope) büyüklüğü ile orantılı olmalı.

```
// KÖTÜ: "5" için arama yapın — binlerce sonuç!
for (int j = 0; j < 34; j++) {
    s += (t[j] * 4) / 5;
}

// İYİ
const REAL_DAYS_PER_IDEAL_DAY = 4;
const WORK_DAYS_PER_WEEK = 5;
for (int j = 0; j < NUMBER_OF_TASKS; j++) {
    let realTaskDays = tasks[j].estimate * REAL_DAYS_PER_IDEAL_DAY;
    let realTaskWeeks = realTaskDays / WORK_DAYS_PER_WEEK;
    sum += realTaskWeeks;
}
```

### Kural 6: Avoid Encodings

Hungarian Notation, member prefix'leri modern IDE'lerde gereksizdir:

```
// KÖTÜ
String strName;
int iAge;
String m_description;

// İYİ
String name;
int age;
String description;
```

### Kural 7: Class Names = Nouns

```
// KÖTÜ              // İYİ
class Process { }    class Customer { }
class Manager { }    class WikiPage { }
class Data { }       class AddressParser { }
```

### Kural 8: Method Names = Verbs

```
// KÖTÜ              // İYİ
function data() { }       function getData() { }
function conflict() { }   function detectConflict() { }

// Boolean: soru formu
if (account.isActive()) { }
if (user.hasPermission("admin")) { }

// Static Factory Method
Complex point = Complex.fromRealNumber(23.0);
```

### Kural 9: Pick One Word Per Concept

```
// KÖTÜ: Aynı şey için üç farklı kelime
userRepository.fetch(id);
orderRepository.retrieve(id);
productRepository.get(id);

// İYİ: Tutarlı tek kelime
userRepository.findById(id);
orderRepository.findById(id);
productRepository.findById(id);
```

### Kural 10: Don't Pun

Aynı kelimeyi farklı kavramlar için kullanma.

```
// KÖTÜ: "add" iki farklı anlama geliyor
class Calculator { int add(int a, int b) { } }     // toplama
class ShoppingCart { void add(Item item) { } }      // koleksiyona ekleme

// İYİ
class Calculator { int add(int a, int b) { } }
class ShoppingCart { void insert(Item item) { } }
```

### Kural 11: Use Solution Domain Names

Kodunuzu okuyanlar programcılar. Teknik terimleri rahatça kullanabilirsiniz:

```
AccountVisitor        // Visitor pattern
JobQueue              // Queue veri yapısı
ConflictObserver      // Observer pattern
```

### Kural 12: Use Problem Domain Names

Teknik terim yoksa, işin uzmanlarının dilini kullanın:

```
class Clearance { }        // Havacılık terimi
class HoldingPoint { }     // Havacılık terimi
class Invoice { }          // Finans terimi
```

### Kural 13: Add Meaningful Context

```
// KÖTÜ: "state" ne anlama geliyor?
String state;

// İYİ: Sınıf ile bağlam oluştur
class Address {
    String street;
    String city;
    String state;   // Burada açık çünkü Address sınıfının içinde
}
```

### Kural 14: Don't Add Gratuitous Context

```
// KÖTÜ: Her sınıfa uygulama prefix'i
class GSDAccountAddress { }
class GSDCustomerContact { }

// İYİ
class AccountAddress { }
class CustomerContact { }
```

## Anti-Pattern'ler

| Anti-Pattern | Neden Kötü | Çözüm |
|--------------|------------|-------|
| Tek harfli değişkenler (`x`, `n`) | Aranamaz, anlam ifade etmez | Kapsam genişse tam isim kullan |
| Kısaltmalar (`calc`, `mgr`) | Belirsiz | `calculate`, `manager` |
| Sayı serileri (`a1`, `a2`) | Tamamen anlamsız | `source`, `destination` |
| Gürültü kelimeleri (`data`, `info`) | Ayırım yaratmaz | Spesifik isim |
| Mental mapping (`r = url`) | Okuyucu sürekli çevirisi yapmak zorunda | Anlamlı isim |

## AI Agent İçin Kontrol Listesi

- [ ] Her değişken, fonksiyon ve sınıf ismi niyeti açıklıyor mu?
- [ ] Yanıltıcı isim var mı?
- [ ] Aynı kavram için tutarlı tek kelime mi kullanılıyor?
- [ ] Sınıf isimleri isim (noun), metot isimleri fiil (verb) mi?
- [ ] Tek harfli değişken döngü dışında kullanılmış mı?
- [ ] Sihirli sayılar sabit olarak tanımlanmış mı?
- [ ] İsimler telaffuz edilebilir ve aranabilir mi?
- [ ] Domain terimleri doğru kullanılmış mı?
