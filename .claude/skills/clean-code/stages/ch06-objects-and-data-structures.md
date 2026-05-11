# Chapter 6: Objects and Data Structures

> "Objects hide their data behind abstractions and expose functions that operate on that data. Data structures expose their data and have no meaningful functions." — Robert C. Martin

## Özet

Nesneler ve veri yapıları birbirinin tersidir. Nesneler veriyi gizler, davranışı açar; veri yapıları veriyi açar, anlamlı davranışı yoktur. Yanlış seçim "hybrid" canavarlara yol açar.

## Data/Object Anti-Symmetry

| İşlem | Prosedürel | Nesne Yönelimli |
|-------|------------|-----------------|
| Yeni fonksiyon ekle | **Kolay** — sadece fonksiyon ekle | Zor — tüm sınıflar değişmeli |
| Yeni tip ekle | Zor — tüm fonksiyonlar değişmeli | **Kolay** — yeni sınıf ekle |

> Her şey nesne olmalı demek bir yanılgıdır. Bazen basit veri yapıları + prosedürel fonksiyonlar en doğru çözümdür.

## Law of Demeter — "Don't Talk to Strangers"

Bir metod yalnızca şu nesnelerin metodlarını çağırabilir:
1. Kendi sınıfının (`this`)
2. Parametreleri
3. Oluşturduğu nesneler
4. Instance değişkenleri

```
// YASAK: Yabancıya konuşma
parameter.getChild().method();

// İZİN VERİLEN
this.method();
parameter.method();
new MyObject().method();
this.instanceVar.method();
```

## Train Wrecks

```
// KÖTÜ: Train Wreck
final String outputDir = ctxt.getOptions().getScratchDir().getAbsolutePath();

// İYİ: Nesneye ne istediğini söyle
BufferedOutputStream bos = ctxt.createScratchFileStream(classFileName);
```

## Hybrids — YAPMA

Yarı nesne yarı veri yapısı = her iki yaklaşımın da en kötü yanları. Ya nesne ol (veriyi gizle, davranışı aç) ya veri yapısı ol (veriyi aç, davranış ekleme).

## Tell, Don't Ask

```
// KÖTÜ: Yapıyı sorguluyor
if (track.getPosition().getLatitude() > runway.getThreshold().getLatitude()) { }

// İYİ: Davranışı nesneye bırak
if (track.hasPassedThreshold(runway)) { }
```

## Data Transfer Objects (DTO)

DTO, saf veri taşıyıcısıdır. İş mantığı olmaz.

```java
public record TrackUpdate(String trackId, double latitude, double longitude, boolean onGround) {}
```

```python
@dataclass
class TrackUpdate:
    track_id: str
    latitude: float
    longitude: float
    on_ground: bool
```

## AI Agent İçin Kontrol Listesi

- [ ] Sınıf veri mi gizliyor, davranış mı açıyor? (Nesne) Yoksa veri mi açıyor? (Veri yapısı)
- [ ] Getter zincirleri var mı? Train wreck kontrolü yap
- [ ] Hybrid oluşmuş mu? Hem public veri hem iş mantığı olan sınıf var mı?
- [ ] DTO'lara iş mantığı eklenmiş mi?
- [ ] Law of Demeter ihlali var mı?
- [ ] "Tell, Don't Ask" prensibi uygulanmış mı?
- [ ] Trade-off analizi yapıldı mı? (Yeni tip mi eklenecek → OOP, yeni fonksiyon mu → prosedürel)
