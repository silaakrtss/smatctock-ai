# ADR 0001: hackathon-kapsami-temalar

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** YZTA Hackathon kapsamında PDF'te tanımlı 6 tema alanından **beş
> tema** ele alınır: **Tema 1 (Müşteri İletişimi Otomasyonu), Tema 2 (Ürün ve
> Sipariş Takibi), Tema 3 (Kargo Süreçlerinin Yönetimi), Tema 4 (Stok ve Envanter
> Yönetimi) ve Tema 5 (İş Akışı ve Görev Yönetimi)**. Tema 6 (Analitik) kapsam
> dışıdır.
>
> **Kapsam:** Proje, bu beş temayı tek bir hikâye altında birleştiren bir
> "Kooperatif Operasyon Ajanı" olarak konumlanır — müşteri NL ile sorar, agent
> stok/sipariş/kargo verisine bakar; eşik altı stok veya kargo gecikmesinde
> proaktif aksiyon (bildirim, tedarikçi taslağı) alır; sabah çalışan bir
> scheduler günün özetini üretir.
>
> **Önemli kısıtlar:**
> - Tema 6 (Analitik ve İçgörü Üretimi) **kapsam dışıdır**; demo'da ve sunumda
>   iddia edilmez.
> - Tema 2 için **görsel dashboard** bu ADR'da karar verilmez — veri + API +
>   agent tool calling ile sorgulanabilirlik yeterli sayılır. Görsel UI ayrı bir
>   ADR'a bırakılır.
> - Tema 5 için "iş akışı" iddiası **sabah özet job'ı** + Tema 4'ün eşik
>   tetikleyicisi ile sınırlıdır; karmaşık görev/rol yönetimi yapılmaz.
> - Beş temanın **tek demo akışında** birbirine bağlanması gerekir; bağımsız
>   feature'lar olarak sunmak yasak.

## Context

YZTA Hackathon "Temalar" dökümanı (PDF) altı tema alanı tanımlıyor ve
katılımcılardan **bir veya birkaçını** kapsayan çözüm bekliyor:

1. Müşteri İletişimi Otomasyonu
2. Ürün ve Sipariş Takibi
3. Kargo Süreçlerinin Yönetimi
4. Stok ve Envanter Yönetimi
5. İş Akışı ve Görev Yönetimi
6. Analitik ve İçgörü Üretimi (opsiyonel)

Hedef kitle: 20–200 ürünlü küçük e-ticaret, butik firmalar, **tarım/gıda/el
sanatları kooperatifleri**, karma yapılar. Mevcut domain modeli (Domates,
Salatalık, Patates) doğrudan kooperatif senaryosuna oturuyor.

Acı noktası: Hackathon süresi sınırlı. Altı temayı da yüzeysel ele almak yerine
**daha derin entegrasyon + aksiyon alabilen agent** vurgusu, PDF'in "sadece
bilgi sunan değil, işlem gerçekleştirebilen sistemler" beklentisine daha iyi
cevap verir. Diğer yandan; Tema 2 (sipariş takibi) ve Tema 5 (iş akışı), Tema
1/3/4'ün doğal yan ürünü olarak çok düşük ek maliyetle iddia edilebilir
durumda — bu nedenle dışarıda bırakmak kapsam puanı kaybı olur.

Gereksinim: Seçilen temalar **doğal bir hikâye** anlatmalı, demo'da tek akışta
birbirine bağlanabilmeli.

## Decision

Beş tema seçilir ve tek bir agent etrafında birleştirilir:

1. **Tema 1 — Müşteri İletişimi Otomasyonu:** NL anlayan, tool calling ile
   sipariş/stok/kargo verisine erişen ve gerektiğinde aksiyon alan agent.
2. **Tema 2 — Ürün ve Sipariş Takibi:** Sipariş listeleme (durum/tarih filtreli),
   tek sipariş detayı + durum geçmişi, "bugün/bekleyen/teslim edilecek"
   sorgularını destekleyen API uçları. Agent bu uçları tool calling ile çağırır.
3. **Tema 3 — Kargo Süreçlerinin Yönetimi:** Kargo durumu takibi, gecikme tespit
   ve hem müşteriye hem yöneticiye proaktif bildirim.
4. **Tema 4 — Stok ve Envanter Yönetimi:** Eşik altı stok tespiti, yenileme
   miktarı önerisi, tedarikçiye taslak sipariş üretimi.
5. **Tema 5 — İş Akışı ve Görev Yönetimi:** Sabah çalışan bir scheduler job
   günün siparişlerini analiz edip özet üretir (hazırlanacak paketler, teslim
   rotası kısa listesi). Bu, Tema 4'ün eşik tetikleyici scheduler'ı ile aynı
   altyapıyı paylaşır.

**Kapsam sınırları (açık olarak yasak):**

- Tema 2 için sipariş **oluşturma/düzenleme UI**'ı yapılmaz (manuel DB seed yeterli).
- Tema 2 için müşteri profili / CRM modülü yapılmaz.
- Tema 5 için karmaşık rol/yetki/ekip yönetimi yapılmaz; "özet üretip yöneticiye
  iletme" sınırında kalınır.
- Tema 6 (analitik tahmin, trend) **yapılmaz, iddia edilmez**.
- Görsel dashboard kararı bu ADR'ın dışındadır — ayrı ADR'da konuşulur.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| Tek tema (sadece Tema 1) | Tek başına chatbot izlenimi verir; "aksiyon alabilen sistem" vurgusu zayıf kalır. |
| Altı temanın tamamı | Tema 6 (analitik) ML/forecasting iş yükü getirir; hackathon süresinde derinlik kaybı kesin. |
| Üç tema (1+3+4), Tema 2'yi altyapı sayıp iddia etmemek | İlk plandı; ancak Tema 2 zaten DB+API olarak gelecek — iddia etmemek **bedava puan bırakmak** olur. Demo'da "bugünkü siparişler" sorgusu zaten yapılacak. |
| Dört tema (1+2+3+4), Tema 5'i kapsam dışı bırakmak | Scheduler altyapısı Tema 4 için zaten gelecek; sabah özet job'ı eklemek **çok ucuz**, Tema 5 iddiası neredeyse bedava. |
| Tema 1 + 2 + 6 (sorgu + analitik) | Aksiyon alma yönü zayıf; PDF "bilgi sunan değil işlem yapan" diyor. Analitik opsiyonel. |
| Tema 3 + 4 (kargo + stok), Tema 1'siz | Müşteri etkileşim yüzeyi olmadan demo soğuk kalır; "doğal dil" beklentisi karşılanmaz. |

## Consequences

### Olumlu

- Demo doğal bir hikâye anlatır: müşteri sorar → agent bakar → proaktif aksiyon →
  sabah özet job'ı çevreyi sarar.
- Beş tema iddiası kapsam puanı için güçlü; "tek tema yapıp derinleştik" eleştirisi
  bertaraf edilir.
- "Aksiyon alabilen agent" beklentisi (Tema 1 + 3 + 4 birlikte) net karşılanır.
- Kooperatif domain'i (mevcut sebze örneği) hedef kitleye birebir oturur.
- Tema 2 ve Tema 5, alttaki DB ve scheduler altyapısı zaten Tema 1/3/4 için
  geleceğinden çok düşük ek maliyetle iddia edilebilir.

### Olumsuz

- Tema 6 (analitik tahmin) yok — jüri sorarsa "ML/forecasting hackathon süresine
  sığmıyor, kapsam yerine derinlik seçtik" cevabı verilecek.
- Tema 2'yi iddia etmek demo'da "panel nerede?" sorusunu davet edebilir; cevap:
  "agent tool calling ile bu veriye erişiyor, görsel katman ayrı ADR'da".
- Beş tema iddiası, kapsamı disiplinli tutmayı gerektirir; her tema **gerçekten
  çalışan + demo akışında görünür** olmazsa iddianın kendisi risk olur.
- Tema 5'in "sabah job'ı" minimal kalır; karmaşık iş akışı bekleyen jüri için
  yüzeysel görünebilir — sunumda sınırı açıkça söylemek gerekir.

## Open items

- [ ] README'de "neden bu beş tema, neden Tema 6 yok?" gerekçesini tek paragraflık özet olarak yaz.
- [ ] Demo akış senaryosunu beş temayı zincirleyecek şekilde yazıya dök.
- [ ] Tema 2 ve Tema 5 için kapsam sınırlarını (ne yapılır / ne yapılmaz) bir concept sayfasında netleştir.
- [ ] Seed data planı: en az 3 günlük, ~30 sipariş, çeşitli durumlarda (Hazırlanıyor, Kargoda, Teslim edildi, Gecikme).
- [ ] Frontend / dashboard kararı için ayrı ADR aç (Tema 2'nin görsel katmanı orada konuşulacak).

## Affected areas

- `README.md` — tema kapsamı ve hikâye burada anlatılacak
- `main.py` — mevcut `/chat` ve `/ai-chat` Tema 1'in çekirdeği; tool calling ile genişleyecek
- _gelecek ADR'lar_ — LLM seçimi, agent yaklaşımı, persistans, scheduler, frontend kararları bu ADR'ın altında konumlanır
