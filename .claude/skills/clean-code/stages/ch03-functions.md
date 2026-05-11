# Chapter 3: Functions

> "Functions should do one thing. They should do it well. They should do it only." — Robert C. Martin

## Özet

Fonksiyonlar yazılımın temel yapı taşlarıdır. Bu bölüm fonksiyon tasarımı için çok net kurallar koyar: küçük ol, tek iş yap, tek soyutlama seviyesinde kal, yan etki yapma, komut-sorgu ayrımına uy.

## Temel Kural: KÜÇÜK OL!

| Metrik | Değer |
|--------|-------|
| İdeal uzunluk | 4-5 satır |
| Maksimum uzunluk | 20 satır |
| Ekranda görünür | Bir bakışta anlaşılır |

## Kurallar

### 1. Do One Thing

Bir fonksiyonu tanımlarken "and" kullanıyorsanız, birden fazla iş yapıyordur — bölün!

```
// KÖTÜ: İki iş yapıyor
function validateAndSave(user) {
    if (!user.name) throw new Error("Invalid");
    database.save(user);
}

// İYİ: Her biri tek iş
function validate(user) {
    if (!user.name) throw new Error("Invalid");
}

function save(user) {
    database.save(user);
}
```

### 2. One Level of Abstraction per Function

Fonksiyon içinde yüksek ve düşük seviye karışmamalı:

```
// KÖTÜ: Soyutlama seviyeleri karışık
function renderPage() {
    let html = getPageHtml();                    // Yüksek seviye
    html = html.replace("&", "&amp;");           // Düşük seviye!
    html = html.replace("<", "&lt;");            // Düşük seviye!
    return renderWithTemplate(html);             // Yüksek seviye
}

// İYİ: Tek seviye
function renderPage() {
    let html = getPageHtml();
    html = escapeHtml(html);
    return renderWithTemplate(html);
}
```

### 3. The Stepdown Rule (Gazete Metaforu)

Kod yukarıdan aşağıya bir hikaye gibi okunmalı:

```
// Ana fonksiyon (en üstte)
public void processConflict() {
    validateInput();
    detectConflicts();
    notifyObservers();
}

// 1. çağrılan
private void validateInput() { }
// 2. çağrılan
private void detectConflicts() { }
// 3. çağrılan
private void notifyObservers() { }
```

### 4. Switch Statements

Switch/if-else zincirleri → polimorfizm ile çöz:

```
// KÖTÜ: Switch her tip için
double calculatePay(Employee e) {
    switch (e.type) {
        case HOURLY: return calculateHourlyPay(e);
        case SALARIED: return calculateSalariedPay(e);
        case COMMISSIONED: return calculateCommissionedPay(e);
    }
}

// İYİ: Polimorfizm
interface Employee {
    double calculatePay();
}

class HourlyEmployee implements Employee {
    double calculatePay() { /* ... */ }
}
```

### 5. Function Arguments

| Sayı | İsim | Tavsiye |
|------|------|---------|
| 0 | Niladic | İdeal |
| 1 | Monadic | İyi |
| 2 | Dyadic | Kabul edilebilir |
| 3 | Triadic | Kaçın |
| 4+ | Polyadic | Asla — Parameter Object kullan |

**Common Monadic Forms:**
- Soru sorma: `boolean fileExists("myFile")`
- Dönüşüm: `InputStream fileOpen("myFile")`
- Olay: `void passwordAttemptFailedNTimes(int attempts)`

**Flag Arguments YASAK:**
```
// KÖTÜ
render(true);

// İYİ
renderForSuite();
renderForSingleTest();
```

**Argument Objects:**
```
// KÖTÜ: 4 parametre
Circle makeCircle(double x, double y, double radius, String color);

// İYİ: Parameter Object
Circle makeCircle(Point center, double radius, String color);
```

### 6. Have No Side Effects

Fonksiyon adının söylemediği şeyleri yapma:

```
// KÖTÜ: checkPassword session'ı da initialize ediyor!
boolean checkPassword(String userName, String password) {
    User user = findUser(userName);
    if (user.passwordMatches(password)) {
        Session.initialize();  // GİZLİ YAN ETKİ!
        return true;
    }
    return false;
}

// İYİ: Ya adını değiştir ya ayır
boolean checkPassword(String userName, String password) { }
void initializeSession() { }
```

### 7. Command-Query Separation

Ya bir şey yap, ya bir şey sor — ikisini birden yapma:

```
// KÖTÜ: Hem set ediyor hem sonuç dönüyor
if (set("username", "bob")) { }  // Ne anlama geliyor?

// İYİ: Ayrılmış
if (attributeExists("username")) {
    setAttribute("username", "bob");
}
```

| Tip | Örnek | Dönüş |
|-----|-------|-------|
| Command | `save(user)` | void |
| Query | `isActive()` | boolean/value |

### 8. Prefer Exceptions to Returning Error Codes

```
// KÖTÜ: Error code — if iç içe
if (deletePage(page) == OK) {
    if (registry.deleteRef(page.name) == OK) {
        if (configKeys.delete(page.key) == OK) {
            logger.log("deleted");
        } else { logger.log("config error"); }
    } else { logger.log("ref error"); }
} else { logger.log("delete error"); }

// İYİ: Exception — temiz akış
try {
    deletePage(page);
    registry.deleteRef(page.name);
    configKeys.delete(page.key);
} catch (Exception e) {
    logger.log(e.getMessage());
}
```

### 9. Extract Try/Catch Blocks

Try/catch'i ayrı fonksiyona çıkar:

```
// İYİ: Try/catch ayrı fonksiyonda
public void delete(Page page) {
    try {
        deletePageAndReferences(page);
    } catch (Exception e) {
        logError(e);
    }
}

private void deletePageAndReferences(Page page) {
    deletePage(page);
    registry.deleteRef(page.name);
    configKeys.delete(page.key);
}
```

**Kural:** `try` ile başlayan fonksiyonda, `catch/finally` sonrasında başka bir şey olmamalı.

### 10. DRY (Don't Repeat Yourself)

Tekrar = her değişiklikte N yer değiştirmek. Tekrarı gördüğünde çıkar (extract).

## Anti-Pattern Kataloğu

| Anti-Pattern | Belirti | Çözüm |
|--------------|---------|-------|
| Long Function | 20+ satır | Extract Method |
| Too Many Arguments | 4+ parametre | Parameter Object |
| Flag Argument | `boolean` parametre | İki ayrı fonksiyon |
| Side Effect | Adında olmayan iş | Adı değiştir veya ayır |
| Command-Query Mix | Hem yapar hem döner | Ayır |
| Output Argument | `appendFooter(report)` | `report.appendFooter()` |
| Dead Function | Hiç çağrılmıyor | Sil |
| Nested Try/Catch | İç içe hata yönetimi | Extract method |

## AI Agent İçin Kontrol Listesi

- [ ] Fonksiyon ≤20 satır mı?
- [ ] Tek iş mi yapıyor? ("and" testi)
- [ ] Tek soyutlama seviyesinde mi?
- [ ] ≤3 argüman mı?
- [ ] Flag (boolean) argüman var mı? → Ayır
- [ ] Gizli yan etki var mı?
- [ ] Command-Query ayrımına uyuyor mu?
- [ ] Try/catch ayrı fonksiyona çıkarılmış mı?
- [ ] Tekrarlanan kod var mı? → DRY
- [ ] Stepdown Rule uygulanmış mı? (çağıran üstte, çağrılan altta)
