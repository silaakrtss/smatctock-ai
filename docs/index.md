# Documentation Index

Tüm proje dokümantasyonunun haritası. Klasör rolleri:

| Klasör | Rol |
|--------|-----|
| [`decisions/`](decisions/) | ADR — mimari kararlar (immutable; supersede ile değişir) |
| [`concepts/`](concepts/) | Yaşayan referans — çapraz-modül disiplin, harita, kataloglar |

---

## Architecture Decision Records (ADR)

Yeni karar eklendiğinde buraya satır eklenir.

### Accepted

| # | Başlık | Tarih |
|---|--------|-------|
| [0001](decisions/0001-hackathon-kapsami-temalar.md) | Hackathon kapsamı — Tema 1, 2, 3, 4, 5 | 2026-05-11 |
| [0002](decisions/0002-mimari-yaklasim-layered-agent.md) | Mimari yaklaşım — layered + ayrı agent katmanı | 2026-05-11 |
| [0003](decisions/0003-cerceve-teknoloji-yigini.md) | Çerçeve teknoloji yığını — FastAPI, Pydantic v2, httpx, test stack | 2026-05-11 |
| [0004](decisions/0004-agent-cercevesi-langchain-langgraph-kullanilmamasi.md) | Agent çerçevesi — LangChain/LangGraph kullanılmaması | 2026-05-11 |
| [0005](decisions/0005-llm-saglayici-secimi-minimax-gemini.md) | LLM sağlayıcı — MiniMax M2.7 birincil, Gemini Flash fallback | 2026-05-11 |
| [0006](decisions/0006-persistans-sqlite-sqlalchemy-imperative-mapping.md) | Persistans — SQLite + SQLAlchemy async + imperative mapping | 2026-05-11 |
| [0007](decisions/0007-scheduler-apscheduler-async.md) | Scheduler — APScheduler 4 async, in-process, hibrit job mimarisi | 2026-05-11 |
| [0008](decisions/0008-notifier-telegram-frontend-sse.md) | Notifier — Telegram + Frontend (SSE), paralel fanout | 2026-05-11 |
| [0009](decisions/0009-agent-loop-tool-calling.md) | Agent loop — basit tool-calling döngüsü, registry dispatcher, RAG yok | 2026-05-11 |
| [0010](decisions/0010-frontend-htmx-alpine-tailwind.md) | Frontend — HTMX + Alpine.js + Jinja2 + Tailwind CDN, multi-page, custom tasarım | 2026-05-11 |
| [0011](decisions/0011-tdd-refactor-disiplini.md) | TDD refactor disiplini — zorunlu kapı, yaşayan checklist | 2026-05-11 |

### Superseded

_Yok._

### Proposed

_Yok._

---

## Concepts

`concepts/` altındaki yaşayan kavram sayfaları (ADR'ların aksine güncellenebilir):

| Sayfa | Açıklama |
|-------|----------|
| [tdd-refactor-checklist](concepts/tdd-refactor-checklist.md) | TDD refactor adımında bakılacaklar — tam liste + 30 sn hızlı tarama (ADR-0011) |
| [demo-akisi](concepts/demo-akisi.md) | Sunumda izlenebilecek tek hikâye — beş tema, adım adım ADR referansı |
| [debug-setup-and-database](concepts/debug-setup-and-database.md) | Kurulum, Alembic migration, seed, SQLite kilidi (ADR-0006) |
| [debug-llm-operations](concepts/debug-llm-operations.md) | LLM kotası, agent loop limiti, `logs_llm/`, `<think>` sanitizer (ADR-0005, ADR-0009) |
| [debug-frontend-behavior](concepts/debug-frontend-behavior.md) | Dashboard SSE, markdown render, sessionStorage, palette (ADR-0010) |
