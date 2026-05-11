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

<!-- TODO: red-green-refactor disiplini, fake stratejisi, IT zorunluluğu.
Skill: tdd-workflow, python-testing -->

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
