# Chapter 12: Emergence

> "By faithfully following the practice of simple design, a developer can avoid getting bogged down." — Robert C. Martin

## Özet

Kent Beck'in dört basit tasarım kuralı sayesinde iyi tasarım "ortaya çıkar" (emerge eder). Bu kurallar öncelik sırasıyla uygulanır.

## Kent Beck'in 4 Kuralı

| Öncelik | Kural | Anlamı |
|---------|-------|--------|
| 1 (En yüksek) | **Runs All the Tests** | Çalıştığını kanıtla |
| 2 | **No Duplication (DRY)** | Tekrarı yok et |
| 3 | **Expresses Intent** | Niyetini açıkça ifade et |
| 4 (En düşük) | **Minimal Classes/Methods** | Gereksiz yapıları yaratma |

### Kural 1: Runs All the Tests

Test yazma disiplini iyi tasarıma iter:
- Test edilebilir olmak için → küçük, tek sorumluluklu sınıflar (SRP)
- Test edilebilir olmak için → bağımlılıkların inject edilebilmesi (DIP)
- Test edilebilir olmak için → soyutlamalar (Interface'ler)

### Kural 2: No Duplication (DRY)

```
// KÖTÜ: Aynı doğrulama iki yerde
public boolean validateLand(LandClearance c) {
    if (c.getRunway() == null) return false;
    if (c.getTrackId() == null) return false;
    // özel doğrulama
}
public boolean validateTakeOff(TakeOffClearance c) {
    if (c.getRunway() == null) return false;    // TEKRAR!
    if (c.getTrackId() == null) return false;    // TEKRAR!
    // özel doğrulama
}

// İYİ: Ortak mantık çıkarılmış
private boolean hasRequiredFields(Clearance c) {
    return c.getRunway() != null && c.getTrackId() != null;
}
```

**Template Method Pattern** ile üst düzey tekrarı giderme: İki sınıf benzer algoritmaya sahip ama detaylar farklıysa, ortak algoritmayı üst sınıfta tanımla, detayları alt sınıflara bırak.

### Kural 3: Expressive

Nasıl ifade edici kod yazılır:
1. **İyi isimler seç**
2. **Fonksiyonları ve sınıfları küçük tut**
3. **Standart pattern isimleri kullan** (Factory, Strategy, Observer)
4. **İyi yazılmış testler kullan** (çalıştırılabilir dokümantasyon)

### Kural 4: Minimal Classes and Methods (YAGNI)

Pragmatik ol, dogmatik olma:
- Her sınıf için interface ZORUNLU değil (tek uygulama varsa)
- "Belki bir gün lazım olur" diye kod yazma
- Kural 4, diğer üç kuraldan düşük öncelikli — sınıf sayısını azaltmak için test kapsamını düşürme

## AI Agent İçin Kontrol Listesi

- [ ] Tüm testler geçiyor mu?
- [ ] Kod tekrarı var mı?
- [ ] Sınıf/metot isimleri niyet ifade ediyor mu?
- [ ] Gereksiz soyutlama var mı? (tek uygulama için interface)
- [ ] Kullanılmayan kod (dead code) var mı?
- [ ] "Belki lazım olur" diye yazılmış kod var mı?
- [ ] Refactoring sonrası testler hâlâ geçiyor mu?
