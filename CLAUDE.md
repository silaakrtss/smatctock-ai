# YZTA_hackathon

Python + FastAPI projesi.

## Build & Test

<!-- TODO: çalıştırma ve test komutları -->

## Code Navigation

<!-- TODO: hangi araçla ne aranır -->

## Mandatory Approaches

Aşağıdaki disiplinler her değişiklikte uygulanır. Detay için ilgili
skill'i çağır; özet/cevap buradan değil skill'den gelmeli.

### 1. Clean Code

<!-- TODO: proje-özgü limit ve kurallar.
Global: ~/.claude/rules/clean-code.md
Skill: coding-standards -->

### 2. TDD (Test-Driven Development)

Red → Green → **Refactor**. Üçüncü adım atlanmaz; yeşil test tek başına
"bitti" değildir (ADR-0011).

Refactor anında her tur şu **hızlı tarama**dan geçer (30 sn):

1. Duplikasyon var mı? (kod + bilgi/magic number)
2. Her isim niyetini söylüyor mu? (`tmp`, `data`, `result` yasak)
3. Hiçbir fonksiyon 20 satırı, sınıf 200 satırı geçmiyor mu?
4. Magic number / flag arg / `None` return / yutulmuş exception yok mu?
5. Test adı davranışı anlatıyor mu? (Arrange uzun mu?)

Detaylı checklist (9 başlık) ve gerekçe:
[`docs/concepts/tdd-refactor-checklist.md`](docs/concepts/tdd-refactor-checklist.md)
— [ADR-0011](docs/decisions/0011-tdd-refactor-disiplini.md).

Kurallar:
- Davranış değişikliği ile refactor **aynı commit'e** girmez
  (`feat:`/`fix:` vs `refactor:`).
- Refactor için **yeni test yazılmaz**; yeni davranış yeni Red turudur.
- Test dosyaları da refactor kapsamındadır.

Skill: `tdd-workflow`, `python-testing`, `clean-code`.

### 3. Python Patterns

<!-- TODO: PEP 8, type hints, idiomatik Python kuralları.
Skill: python-patterns -->

### 4. API Design

<!-- TODO: REST/FastAPI endpoint, status code, error response konvansiyonları.
Skill: api-design -->

## Python / FastAPI

<!-- TODO: dil ve framework idiom'ları -->

## Git Commit Convention

<!-- TODO: commit format, AI signature politikası -->

## Gotchas

<!-- TODO: projeye özgü tuzaklar (.env, vectors.db, MiniMax API vb.) -->

## Documentation

<!-- TODO: source of truth, archive konumu -->

## ADR (Architecture Decision Records)

Bu proje ADR disiplinini `adr-kit` plugin'i üzerinden uygular. Kurulum (kullanıcı bazlı):

```
/plugin marketplace add saadettinBerber/adr-kit
/plugin install adr-kit@adr-kit
```

Kurulum sonrası:
- `/adr-kit:adr-init` — `docs/` iskeletini oluşturur
- `/adr-kit:adr-new <başlık>` — yeni ADR
- Skill: `architecture-decision` (mimari sorular otomatik tetikler)

Detay: https://github.com/saadettinBerber/adr-kit
