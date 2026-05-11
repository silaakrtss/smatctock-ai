# Chapter 10: Classes

> "The first rule of classes is that they should be small. The second rule of classes is that they should be smaller than that." — Robert C. Martin

## Özet

Sınıf tasarımında boyut satır sayısıyla değil sorumluluk sayısıyla ölçülür. SRP, yüksek cohesion, OCP ve DIP bu bölümün dört ana direğidir.

## Sınıf Organizasyonu

```
public class WellOrganizedClass {
    // 1. Sabitler (public static final)
    // 2. Static değişkenler (private static)
    // 3. Instance değişkenleri (private)
    // 4. Constructor'lar
    // 5. Public metotlar
    // 6. Private metotlar (çağıran public metottan hemen sonra)
}
```

## Single Responsibility Principle (SRP)

> "Bir sınıfın değişmesi için tek bir neden olmalı."

**25 Kelime Testi:** Sınıfın ne yaptığını "if", "and", "or", "but" kullanmadan 25 kelimeyle açıklayabilmelisiniz.

```
// KÖTÜ: 4 değişim nedeni
public class Employee {
    public double calculatePay() { }     // Maaş kuralları değişirse
    public String generateReport() { }   // Raporlama formatı değişirse
    public void saveToDatabase() { }     // DB şeması değişirse
    public void sendNotification() { }   // Bildirim sistemi değişirse
}

// İYİ: Her sınıf tek sorumluluk
public class PayCalculator { double calculatePay(Employee e) { } }
public class EmployeeReporter { String generateReport(Employee e) { } }
public class EmployeeRepository { void save(Employee e) { } }
public class NotificationService { void send(String to, String msg) { } }
```

## Cohesion (Uyum)

Her metot aynı field'ları kullanmalı. Metotlar farklı değişken alt kümelerini kullanıyorsa → sınıfı böl.

```
// DÜŞÜK COHESION: Email metotları DB değişkenlerini, DB metotları email değişkenlerini kullanmıyor
public class UserManager {
    private EmailClient emailClient;  // Grup A
    private Connection dbConnection;   // Grup B

    public void sendEmail() { }    // Sadece Grup A
    public void saveUser() { }     // Sadece Grup B
}

// İYİ: Her sınıf yüksek cohesion
public class EmailService { /* emailClient kullanır */ }
public class UserRepository { /* dbConnection kullanır */ }
```

## Open/Closed Principle (OCP)

> "Genişletmeye açık, değişikliğe kapalı."

```
// KÖTÜ: Yeni SQL tipi = mevcut sınıf değişir
public class Sql {
    public String create() { }
    public String insert() { }
    public String selectAll() { }
    // UPDATE eklemek = mevcut koda dokunmak
}

// İYİ: Yeni tip = yeni sınıf, mevcut kod değişmez
public abstract class Sql { public abstract String generate(); }
public class CreateSql extends Sql { }
public class SelectSql extends Sql { }
public class InsertSql extends Sql { }
// UPDATE? Sadece yeni sınıf ekle!
```

## Dependency Inversion Principle (DIP)

> "Somut detaylara değil, soyutlamalara bağımlı ol."

```
// KÖTÜ: Somut sınıfa bağımlı
private final HazelcastRepository repository;

// İYİ: Soyutlamaya bağımlı
private final ConflictRepository repository;  // Interface!
```

## Anti-Pattern'ler

| Anti-Pattern | Çözüm |
|--------------|-------|
| God Class (binlerce satır) | SRP uygula, sınıfı böl |
| Feature Envy (başka sınıfın verisiyle çalışıyor) | Metotu doğru sınıfa taşı |
| Data Class (sadece getter/setter) | İlgili davranışı sınıfa ekle |
| Shotgun Surgery (tek değişiklik 10 sınıfı etkiler) | İlgili kodu tek sınıfta topla |

## AI Agent İçin Kontrol Listesi

- [ ] Sınıfın 25 kelimeyle, "and/or/but/if" olmadan açıklanabiliyor mu?
- [ ] Sınıfın değişmesi için tek bir neden var mı? (SRP)
- [ ] Sınıf 200 satırdan kısa mı?
- [ ] Tüm metotlar aynı field'ları kullanıyor mu? (Cohesion)
- [ ] Yeni özellik eklemek mevcut kodu değiştirmeyi gerektiriyor mu? (OCP)
- [ ] Sınıf somut sınıflara mı yoksa soyutlamalara mı bağımlı? (DIP)
- [ ] Train wreck (`a.getB().getC()`) var mı?
