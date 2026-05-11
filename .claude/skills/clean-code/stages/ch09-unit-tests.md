# Chapter 9: Unit Tests

> "Test code is just as important as production code. It requires thought, design, and care." — Robert C. Martin

## Özet

Birim testler, yazılımın esnekliğini ve sürdürülebilirliğini garanti eden temel yapıdır. Kirli testler, test yazmamaktan daha kötüdür. Testler kodu değiştirme cesareti verir.

## TDD'nin 3 Yasası

1. **Fail eden bir test yaz** (derlenmemek de fail'dir)
2. **Testi geçen minimum kodu yaz**
3. **Refactor et** (hem test hem üretim kodunu)

```
RED → GREEN → REFACTOR döngüsü (yaklaşık 30 saniye)
```

## F.I.R.S.T. Prensipleri

| Harf | Prensip | Açıklama |
|------|---------|----------|
| **F** | Fast | Testler milisaniyede çalışmalı — mock kullan |
| **I** | Independent | Testler birbirine bağımlı olmamalı |
| **R** | Repeatable | Her ortamda aynı sonuç — sabit zaman kullan |
| **S** | Self-Validating | Assert kullan, println değil |
| **T** | Timely | Üretim koduyla birlikte yaz |

## Temiz Test = Okunabilirlik

### Given-When-Then Pattern

```
@Test
void shouldDetectConflict_whenSameRunway() {
    // Given (BUILD)
    Clearance land = givenLandClearanceFor("RWY06");
    Clearance takeOff = givenTakeOffClearanceFor("RWY06");

    // When (OPERATE)
    Optional<Conflict> result = detector.evaluate(land, takeOff);

    // Then (CHECK)
    assertThat(result).isPresent();
    assertThat(result.get().getType()).isEqualTo(LAND_VS_TAKE_OFF);
}
```

### Domain-Specific Testing Language (DSL)

```
// DSL ile — bir hikaye gibi okunuyor
ClearanceWithSnapshot landing = aLandClearance()
    .forAircraft("THY123")
    .onRunway("RWY06")
    .build();
```

## Single Concept per Test

Her test tek bir kavramı doğrulamalı:

```
// KÖTÜ: 3 kavram tek testte
@Test void testCalculator() {
    assertEquals(4, calc.add(2, 2));       // Toplama
    assertEquals(0, calc.subtract(2, 2));   // Çıkarma
    assertThrows(..., () -> calc.divide(1, 0)); // Bölme hatası
}

// İYİ: Her kavram kendi testinde
@Test void shouldAddTwoNumbers() { }
@Test void shouldSubtractTwoNumbers() { }
@Test void shouldThrowException_whenDividingByZero() { }
```

## Dual Standard

Test kodu üretim koduyla aynı **kalitede** olmalı, ama aynı **verimlilik** standartlarında olmak zorunda değil. Okunabilirlik her iki kodda da zorunlu.

## Test İsimlendirme

| Pattern | Örnek |
|---------|-------|
| `should[Behavior]_when[Condition]` | `shouldDetectConflict_whenSameRunway` |
| `should[Result]_given[State]` | `shouldReturnEmpty_givenNoActiveClearance` |

## Anti-Pattern'ler

| Anti-Pattern | Çözüm |
|--------------|-------|
| God Test (her şeyi test eder) | Single Concept per Test |
| Dependent Tests (sıralama gerektirir) | Her test kendi state'ini oluşturur |
| Manual Verification (println) | Assert/Verify kullan |
| Slow Tests | Mock/Stub kullan |
| Happy Path Only | Edge case ve hata senaryoları ekle |
| Copy-Paste Tests | Extract method, `@BeforeEach`, DSL |

## AI Agent İçin Kontrol Listesi

- [ ] Her test tek bir kavramı mı test ediyor?
- [ ] Testler Given-When-Then yapısında mı?
- [ ] Test isimleri davranışı açıkça ifade ediyor mu?
- [ ] Testler birbirine bağımlı mı? (shared state yok mu?)
- [ ] Testler herhangi bir ortamda tekrarlanabilir mi?
- [ ] Manuel doğrulama gerekmiyor mu? (println yerine assert)
- [ ] Testler hızlı mı? (< 100ms, mock kullanılmış mı?)
- [ ] Test DSL'i oluşturulmuş mu?
- [ ] Edge case'ler test edilmiş mi?
- [ ] Test kodu üretim kodu kadar temiz mi?
