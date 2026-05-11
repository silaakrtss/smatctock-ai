# Chapter 14: Successive Refinement (Case Study)

> "To write clean code, you must first write dirty code and then clean it." — Robert C. Martin

## Özet

Bu bölüm bir case study'dir. `Args` adlı bir komut satırı argüman parser'ının adım adım refactoring'i anlatılır. Temel ders: **"çalışıyor" demek "bitti" demek değildir**.

## Working Mess → Clean Code Süreci

```
1. "Working Mess" (Çalışan Kaos)
   → Kod çalışıyor ama okunması zor

2. "Recognize the Rot" (Bozulmayı Farket)
   → "Bir tip daha eklersem bu kod çökecek"

3. "Stop Adding Features" (Özellik Eklemeyi Dur)
   → Öncelik: mevcut kodu temizle

4. "Incremental Refactoring" (Adım Adım Temizle)
   → Her adımda testler geçmeli

5. "Clean Code" (Temiz Kod)
   → Yeni özellik eklemek kolay
```

## Altın Kurallar

### TDD Olmadan Refactoring Yapma

Testler güvenlik ağıdır. Her refactoring adımından sonra `mvn test` çalıştır.

### Incrementalism — Küçük Adımlar

```
Adım 1: ArgsException sınıfını çıkar → Testler geçiyor mu? EVET
Adım 2: Boolean parsing'i ayrı sınıfa taşı → Testler geçiyor mu? EVET
Adım 3: String parsing'i ayrı sınıfa taşı → Testler geçiyor mu? EVET
Adım 4: Ortak interface çıkar → Testler geçiyor mu? EVET
```

### Refactoring Stratejileri

| Strateji | Ne Zaman |
|----------|----------|
| **Extract Class** | Büyük sınıf → küçük, odaklı sınıflar |
| **Extract Interface** | if/else zincirleri → polimorfizm |
| **One Thing at a Time** | Her adımda sadece bir concern değiştir |

### if/else → Polimorfizm Örneği

```
// ÖNCE: if/else zinciri
if (isBooleanArg(c)) setBooleanArg(c);
else if (isStringArg(c)) setStringArg(c);
else if (isIntArg(c)) setIntArg(c);

// SONRA: Polimorfizm
interface ArgumentMarshaler {
    void set(Iterator<String> args);
    Object get();
}
class BooleanArgumentMarshaler implements ArgumentMarshaler { }
class StringArgumentMarshaler implements ArgumentMarshaler { }
class IntegerArgumentMarshaler implements ArgumentMarshaler { }
```

## Pratik Dersler

| Ders | Açıklama |
|------|----------|
| İlk taslak çirkin olabilir | Önemli olan orada kalmamak |
| Testler olmazsa refactoring yapılmaz | Güvenlik ağı olmadan cesaret değil, dikkatsizlik |
| Küçük adımlarla ilerle | Büyük "sil baştan yazma" projeleri başarısıza mahkum |
| "Çalışıyor" yeterli değil | Çalışan ama okunmayan kod zamanla çöker |
| Refactoring bir lüks değil | Profesyonel yazılımcının günlük işi |

## AI Agent İçin Kontrol Listesi

- [ ] Yeni özellik eklerken mevcut kod karmaşıklaşıyorsa → önce refactor et
- [ ] Refactoring yapmadan önce yeterli test coverage var mı?
- [ ] Her refactoring adımında testler geçiyor mu?
- [ ] if/else zincirleri var mı? → Polimorfizme geçir
- [ ] Büyük sınıflar var mı? → Extract Class uygula
- [ ] "Çalışan ama çirkin" kodu kabul müyüz? → Kabul edilemez, temizle
- [ ] `mvn test` her commit'ten önce çalışıyor mu?
