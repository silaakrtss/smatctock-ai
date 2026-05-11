# Chapter 8: Boundaries

> "Code at the boundaries needs clear separation and tests that define expectations." — Robert C. Martin

## Özet

Dış kodu (üçüncü parti kütüphaneler, henüz yazılmamış modüller, harici API'ler) kendi kodumuzdan izole etmek temiz kodun kritik alanıdır.

## Kurallar

### 1. Wrap Third-Party Code

```
// KÖTÜ: Map her yere geçiriliyor
Map<String, Sensor> sensors = new HashMap<>();
sensors.clear();       // Herkes her şeyi yapabilir!

// İYİ: Wrapper sınıf ile sarmala
public class Sensors {
    private final Map<String, Sensor> sensors = new HashMap<>();
    public Sensor getById(String id) { return sensors.get(id); }
    public void register(String id, Sensor sensor) { sensors.put(id, sensor); }
    // clear(), remove() gibi tehlikeli işlemler AÇILMADI
}
```

### 2. Learning Tests

Üçüncü parti kütüphaneleri entegre etmeden önce **learning test** yaz:

```
// Kütüphanenin davranışını testlerle öğren
@Test void testLogWithLayout() {
    Logger logger = Logger.getLogger("MyLogger");
    logger.addAppender(new ConsoleAppender(new PatternLayout("%p %t %m%n")));
    logger.info("Hello");
    // Şimdi düzgün çalışıyor!
}
```

**Avantajları:**
- Kontrollü öğrenme (deneme-yanılma yerine)
- Kütüphane güncellendiğinde erken uyarı (regresyon testi)
- Canlı dokümantasyon

### 3. Code That Does Not Yet Exist

Bağımlılığın henüz hazır değilse: **kendi arayüzünü tanımla**.

```
// Kendi arayüzümüz
public interface Transmitter {
    void transmit(Frequency frequency, DataStream stream);
}

// Test için fake
public class FakeTransmitter implements Transmitter { }

// Gerçek API geldiğinde — sadece Adapter yaz
public class RealTransmitterAdapter implements Transmitter {
    public void transmit(Frequency freq, DataStream stream) {
        thirdPartyApi.send(freq.toHz(), stream.toBytes());
    }
}
```

### 4. Adapter Pattern

```
Bizim Kodumuz ──► [Arayüz] ◄── Adapter ──► Üçüncü API
                  (bizim)      (tek nokta)   (dışarı)

API değişirse: SADECE Adapter değişir
```

## AI Agent İçin Kontrol Listesi

- [ ] Üçüncü parti tipler doğrudan public API'de mi? → Sarmala
- [ ] Dış kütüphane kullanılıyorsa Adapter/Wrapper var mı?
- [ ] Learning test'ler var mı?
- [ ] Henüz hazır olmayan bağımlılıklar için interface tanımlanmış mı?
- [ ] Sınır arayüzleri sınıfın içinde mi tutulmuş?
- [ ] Adapter tek noktada mı?
