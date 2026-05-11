# Chapter 4: Comments

> "Don't comment bad code — rewrite it." — Brian W. Kernighan and P. J. Plaugher

> "Comments are, at best, a necessary evil." — Robert C. Martin

## Özet

Yorumlar kodun yetersizliğini telafi etmek için yazılır. Yorum yazmadan önce şunu sorun: "Bu kodu yorum gerektirmeyecek kadar açık yazabilir miyim?" Cevap çoğu zaman evettir.

## Temel Prensip

```
// KÖTÜ: Kötü kodu yorumla "açıklama"
// Check to see if the employee is eligible for full benefits
if ((employee.flags & HOURLY_FLAG) && (employee.age > 65)) { }

// İYİ: Kod kendini açıklıyor
if (employee.isEligibleForFullBenefits()) { }
```

## İyi Yorumlar (Good Comments)

| Tür | Açıklama | Örnek |
|-----|----------|-------|
| **Legal** | Telif hakkı/lisans | `// Copyright (C) 2024 by Company` |
| **Informative** | Teknik bilgi (regex format vb.) | `// format: kk:dd:ss EEE, MMM dd, yyyy` |
| **Intent** | "Neden" açıklaması | `// We use insertion sort because data is nearly sorted` |
| **Clarification** | Değiştirilemez 3. parti kod davranışı | `// compareTo returns: a > b -> 1` |
| **Warning** | Sonuç uyarısı | `// WARNING: Not thread-safe` |
| **TODO** | Ticket numaralı yapılacak | `// TODO: JIRA-1234 - Remove after migration` |
| **Amplification** | Gözden kaçabilecek önemli detay | `// The trim() is critical: library returns trailing newlines` |

## Kötü Yorumlar (Bad Comments)

| Tür | Neden Kötü | Çözüm |
|-----|------------|-------|
| **Redundant** | Kodun söylediğini tekrarlıyor | Kodu daha açık yaz, yorumu sil |
| **Misleading** | Yanlış bilgi veriyor | Tehlikeli — bug kaynağı |
| **Mandated** | Kural gereği yazılmış ama değer katmıyor | Public API hariç Javadoc yazma |
| **Journal** | Değişiklik günlüğü | `git log` kullan |
| **Noise** | `/** Default constructor */` | Sil |
| **Position Markers** | `// ======= Actions =======` | Nadir kullan |
| **Closing Brace** | `} // end while` | Fonksiyonu kısalt |
| **Attributed** | `// Added by: John` | `git blame` kullan |
| **Commented-Out Code** | Yorum satırına alınmış kod | Sil, VCS hatırlıyor |
| **Too Much Info** | Mini makale olmuş | Referans ver, essay yazma |
| **Mumbling** | Belirsiz, sadece yazar anlar | Net yaz veya yazma |

## AI Agent İçin Kontrol Listesi

- [ ] Yorum yazmadan önce: "Bu kodu yorum gerektirmeyecek kadar açık yazabilir miyim?"
- [ ] Yorum "ne" değil "neden" açıklıyor mu?
- [ ] Redundant yorum var mı? (kodun zaten söylediğini tekrar eden)
- [ ] Commented-out code var mı? (varsa sil)
- [ ] TODO yorumlarında ticket numarası var mı?
- [ ] Journal comments var mı? (varsa sil)
- [ ] Yanıltıcı yorum var mı? (kodla uyuşmuyor)
- [ ] Closing brace comment var mı? (varsa fonksiyonu kısalt)
- [ ] Gürültü yorumları var mı?
