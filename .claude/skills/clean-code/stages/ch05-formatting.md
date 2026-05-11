# Chapter 5: Formatting

> "Code formatting is about communication, and communication is the professional developer's first order of business." — Robert C. Martin

## Özet

Kod biçimlendirme bir tercih meselesi değil, bir iletişim aracıdır. Kodu bir gazete makalesi gibi organize edin: başlık (sınıf adı), özet (public metotlar), detaylar (private metotlar).

## Dikey Biçimlendirme (Vertical Formatting)

### Newspaper Metaphor (Gazete Metaforu)

```
class ConflictDetectionService {
    // BAŞLIK + ÖZET (public API)
    public ConflictResult detectConflicts(Clearance newClearance) { }

    // ORTA SEVİYE DETAYLAR
    private ConflictResult evaluateAgainstExisting(...) { }
    private Optional<Conflict> findConflict(...) { }

    // EN DÜŞÜK SEVİYE DESTEK
    private List<Clearance> findActiveClearances() { }
}
```

### Vertical Openness (Kavramlar Arası Boşluk)

Boş satırlar farklı kavramları birbirinden ayırır:
- Package tanımından sonra
- Import bloğundan sonra
- Metotlar arasında
- Bir metot içinde farklı mantıksal adımlar arasında

### Vertical Distance (Dikey Mesafe)

- **Değişken tanımları:** Kullanıldıkları yere yakın
- **Instance değişkenleri:** Sınıfın en üstünde
- **Bağımlı fonksiyonlar:** Çağırıcı üstte, çağrılan altta, yakın
- **Kavramsal yakınlık:** İlişkili fonksiyonlar (assert ailesi gibi) birbirine yakın

### Vertical Ordering (Dikey Sıralama)

```
Yüksek seviye (soyut)      ← Dosyanın üstü
    |
    v
Orta seviye
    |
    v
Düşük seviye (detay)       ← Dosyanın altı
```

## Yatay Biçimlendirme (Horizontal Formatting)

### Boşluk Kullanımı

| Durum | Boşluk | Örnek |
|-------|--------|-------|
| Atama operatörü | Var | `x = 5` |
| Fonksiyon adı + parantez | Yok | `doSomething()` |
| Argümanlar arası | Var (virgülden sonra) | `func(a, b, c)` |

### Horizontal Alignment — YAPMA

```
// KÖTÜ: Göz önemli bilgiyi atlıyor
private   String      name;
private   int         age;
protected boolean     isActive;

// İYİ: Doğal okuma
private String name;
private int age;
protected boolean isActive;
```

### Satır Genişliği: 120 karakter sınırı

### Girintileme: Her zaman girinti + süslü parantez kullan

```
// KÖTÜ
if (condition) doSomething();

// İYİ
if (condition) {
    doSomething();
}
```

## Dosya Boyutu

Çoğu dosya 200 satırın altında olmalı. 500 satırı geçen dosyalar sınıf bölmeye aday.

## Takım Kuralları

Bireysel tercihler takım kararının gerisinde kalır. Seçim ne olursa olsun, **tutarlılık** önemlidir. IDE formatter konfigürasyonunu takımca paylaşın.

## AI Agent İçin Kontrol Listesi

- [ ] Dosya gazete metaforu izliyor mu? (public üstte, private altta)
- [ ] Kavramlar arası boş satır var mı?
- [ ] İlişkili kodlar birbirine yakın mı?
- [ ] Çağırıcı fonksiyon çağrılanın üstünde mi?
- [ ] Satır uzunluğu 120 karakteri geçiyor mu?
- [ ] Dosya boyutu 200 satırı geçiyor mu?
- [ ] Instance değişkenler sınıfın üstünde mi?
- [ ] Girintileme tutarlı mı?
- [ ] Kısa bloklar bile süslü parantez içinde mi?
