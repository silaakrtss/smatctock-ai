# Chapter 11: Systems

> "Software systems should separate the startup process, when the application objects are constructed and the dependencies are 'wired' together, from the runtime logic that takes over after startup." — Robert C. Martin

## Özet

Nesne yaratma (construction) ile nesne kullanımı (use) birbirinden ayrılmalıdır. Dependency Injection, Factory Pattern ve Cross-Cutting Concerns ile ölçeklenebilir, test edilebilir ve evrimleşebilir sistemler inşa edilir.

## Kurallar

### 1. Separate Construction from Use

```
// KÖTÜ: Construction ve use iç içe
public class TrackService {
    public GeoCalculator getGeoCalculator() {
        if (geoCalculator == null) {
            geoCalculator = new GeoCalculator(new EarthConstants());
        }
        return geoCalculator;
    }
}

// İYİ: Sadece kullanıyor
@RequiredArgsConstructor
public class TrackService {
    private final GeoCalculator geoCalculator;
}
```

### 2. Dependency Injection

| Özellik | Constructor Injection | Field Injection |
|---------|-----------------------|-----------------|
| Immutability | `final` kullanılabilir | Kullanılamaz |
| Test | Kolay mock | Reflection gerekir |
| Görünürlük | Bağımlılıklar açıkça görünür | Gizli |

### 3. Factories

Uygulama nesne yaratma **zamanlamasını** kontrol etmeli ama **detaylarını** bilmemeli.

### 4. Cross-Cutting Concerns (AOP)

```
// KÖTÜ: Logging her metotta tekrarlanıyor
public Optional<ConflictContext> detect(...) {
    log.info("started");
    StopWatch watch = new StopWatch();
    // ... iş mantığı logging ile karışık
}

// İYİ: AOP ile ayrılmış
@Timed
public Optional<ConflictContext> detect(...) {
    return ruleEngine.evaluate(...);
}
```

### 5. Evrimsel Mimari

BDUF (Big Design Up Front) yerine: basit başla, ihtiyaç oldukça büyüt. Interface'ler üzerinden çalışırsan, alttaki teknolojiyi değiştirmek kolay.

### 6. Kararları Ertele

Erken karar = az bilgiyle karar = yüksek risk. Interface arkasına gizle, en son sorumlu anda karar ver.

## AI Agent İçin Kontrol Listesi

- [ ] Nesne yaratma (`new`) uygulama kodunun içinde mi? → DI'ya taşı
- [ ] Cross-cutting concern'ler iş mantığına karışmış mı? → AOP düşün
- [ ] Mimari kararlar çok erken mi alınmış? → Interface arkasına gizle
- [ ] Bağımlılıklar constructor injection ile mi enjekte ediliyor?
- [ ] `@Autowired` field injection kullanılmış mı? → Constructor injection'a çevir
