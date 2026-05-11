# ADR NNNN: [Kısa Başlık]

- Status: Proposed | Accepted | Superseded
- Date: YYYY-MM-DD
- Supersedes: - | ADR-XXXX
- Superseded-by: - | ADR-XXXX

## TL;DR (özet istendiğinde bunu alıntıla)

> Kararın 2-5 satırlık özü. AI asistan bu bloğu kullanıcıya **birebir
> alıntılayacak**, bu yüzden tek başına anlamlı olmalı.
>
> İyi bir TL;DR şunları içerir:
> - **Karar:** Ne yapıldı? (Tek cümle, kalın vurguyla)
> - **Kapsam:** Hangi modül/katman/bağlam etkilenir?
> - **Önemli kısıtlar:** "X yasak", "Y zorunlu" gibi kuralları açıkça yaz.

## Context

Hangi problem bu kararı zorunlu kıldı? Hangi kısıtlar var?

- Mevcut durum nedir?
- Hangi acı noktası bu kararı tetikledi?
- Hangi gereksinimler var?

## Decision

Ne yapıldığı. Tek cümlelik özet + gerekiyorsa detay.

Eğer karar birden çok parçadan oluşuyorsa numaralandır:

1. Birinci karar parçası
2. İkinci karar parçası

## Alternatives considered

Hangi alternatifler değerlendirildi, neden elendi?

| Alternatif | Neden elendi? |
|------------|---------------|
| Alternatif A | ... |
| Alternatif B | ... |

## Consequences

### Olumlu

- ...
- ...

### Olumsuz

- ...
- ...

## Open items

Henüz uygulanmamış veya tamamlandığında referansla işaretlenmiş maddeler.
Format (ADR-0012):

- `[x] Madde. *(Fxx, PR #N — kısa açıklama)*` — tamamlandı, referans şart.
- `[ ] Madde. *(Gerekçe: neden açık)*` — açık, gerekçe şart.

**Silme yalnızca ADR superseded olduğunda.** Aktif ADR'da `[ ]` ve `[x]`
birbirinin yanında yaşar; geçmiş kaybedilmez.

- [ ] ... *(gerekçe)*
- [ ] ... *(gerekçe)*

## Affected areas

- `src/path/to/affected/code` — kısa açıklama
- [[concepts/ilgili-kavram]] — etkilenen concept sayfası
- [[NNNN-related-adr]] — bağlantılı ADR
