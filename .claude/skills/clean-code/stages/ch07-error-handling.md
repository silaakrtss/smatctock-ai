# Chapter 7: Error Handling

> "Error handling is important, but if it obscures logic, it's wrong." — Robert C. Martin

## Özet

Hata yönetimi temiz kodun ayrılmaz bir parçasıdır ancak ana mantığı gölgede bıraktığında amacını yitirir. Exceptions kullanarak hata yönetimini iş mantığından ayırmak, null dönmemek ve özel durumları Special Case Pattern ile ele almak bu bölümün temel mesajlarıdır.

## Temel Prensipler

| Prensip | Kötü | İyi |
|---------|------|-----|
| Exceptions > Return Codes | `if (result == ERROR)` | `throw new InvalidOrderException()` |
| Don't Return Null | `return null` | `return Optional.empty()` |
| Don't Pass Null | `process(null, "data")` | Guard clause veya assertion |
| Context with Exceptions | `throw new Exception("Error")` | `throw new TrackNotFoundException("THY123 not found for RWY05")` |
| Unchecked Exceptions | `throws IOException, SQLException` | Runtime exception hierarchy |

## Kurallar

### Use Exceptions Rather Than Return Codes

```
// KÖTÜ: İş mantığı hata kontrolü içinde kaybolur
int result = bank.withdraw(account, 500);
if (result == 0) { log.info("OK"); }
else if (result == -1) { log.error("Not found"); }

// İYİ: Temiz ve okunabilir
try {
    bank.withdraw(account, 500);
    log.info("OK");
} catch (InsufficientFundsException e) {
    log.error(e.getMessage());
}
```

### Don't Return Null — Use Optional

```
// KÖTÜ
public Track findById(String id) {
    return map.get(id);  // null dönebilir!
}

// İYİ
public Optional<Track> findById(String id) {
    return Optional.ofNullable(map.get(id));
}
```

### Special Case Pattern

```
// KÖTÜ: Exception normal akışı bozuyor
try {
    expenses = dao.getMeals(id);
    total += expenses.getTotal();
} catch (MealExpensesNotFound e) {
    total += getMealPerDiem();
}

// İYİ: Special Case nesnesi
MealExpenses expenses = dao.getMeals(id);
total += expenses.getTotal();
// dao bulamadığında PerDiemMealExpenses döner
```

### Wrap Third-Party Exceptions

```
// İYİ: Üçüncü parti API'yi sarmala
public class LocalPort {
    public void open() {
        try {
            innerPort.open();
        } catch (DeviceResponseException e) {
            throw new PortDeviceException(e);
        } catch (ATM1212UnlockedException e) {
            throw new PortDeviceException(e);
        }
    }
}
```

## Anti-Pattern'ler

| Anti-Pattern | Çözüm |
|--------------|-------|
| `return null` | `Optional.empty()` veya `Collections.emptyList()` |
| Null parametre | Guard clause, `@NonNull` |
| `catch (Exception e) {}` | Spesifik exception yakala, logla |
| Return code ile hata yönetimi | Exception kullan |
| Bağlamsız exception mesajı | İşlem, neden ve değerleri ekle |

## AI Agent İçin Kontrol Listesi

- [ ] Metod `null` dönüyor mu? → `Optional` veya boş koleksiyon
- [ ] Metoda `null` parametre geçilebilir mi? → Guard clause
- [ ] Return code ile hata yönetimi var mı? → Exception'a çevir
- [ ] `catch (Exception e) {}` gibi yutucular var mı?
- [ ] Exception mesajları yeterli bağlam içeriyor mu?
- [ ] Üçüncü parti API exception'ları sarmalı mı?
- [ ] Normal akış içinde exception kullanılıyor mu? → Special Case Pattern
- [ ] Hata yönetimi iş mantığını gölgede bırakmış mı?
