# Kooperatif Operasyon Ajanı — YZTA Hackathon

Tema 1–5'i tek hikâye altında birleştiren proaktif agent. Detay için
`docs/decisions/0001-hackathon-kapsami-temalar.md`.

## Gereksinimler

- Python 3.10+
- MiniMax API anahtarı (birincil LLM — ADR-0005)
- (Opsiyonel) Gemini API anahtarı (fallback)
- (Opsiyonel) Telegram bot token (notifier — ADR-0008)

## 1. Repoyu klonla

```bash
git clone https://github.com/silaakrtss/smatctock-ai.git
cd smatctock-ai
```

## 2. Sanal ortam + bağımlılıklar

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
make install                       # pip install -e ".[dev]"
```

## 3. `.env` dosyasını hazırla

```bash
cp .env.example .env
```

`MINIMAX_API_KEY` zorunlu; diğerleri ileri fazlarda doldurulur.

## 4. Sunucuyu başlat

```bash
make run                           # uvicorn src.presentation.main:app --reload
```

- App: <http://127.0.0.1:8000>
- Health: <http://127.0.0.1:8000/health>

## Geliştirme

```bash
make check        # ruff + format-check + mypy --strict + import-linter + pytest
make test         # sadece test
make lint         # ruff check
make format       # ruff format
make typecheck    # mypy --strict src/
make imports      # lint-imports (katman ihlali kontrolü)
```

CI'da hepsi zorunlu (`.github/workflows/ci.yml`). Coverage eşiği: **%85**
(ADR-0002).

## Proje yapısı

`src/` köklü, 5 katmanlı (ADR-0002):

```
src/
  domain/          # Saf iş kuralları (dataclass, framework yok)
  application/     # Use case'ler + port arayüzleri
    ports/         # Repository, LLMClient, Notifier, Scheduler arayüzleri
    services/      # StockService, OrderService, ...
  agent/           # Tool-calling loop, registry, dispatcher
    tools/         # JSON schema + registry
    prompts/       # Markdown sistem promptları
    workflows/     # Sabah brifingi vb. proaktif akışlar
  infrastructure/  # Port implementasyonları
    db/            # SQLAlchemy async + imperative mapping (ADR-0006)
    llm/           # MiniMax / Gemini adapter'ları (ADR-0005)
    notifiers/     # Telegram, SSE (ADR-0008)
    scheduler/     # APScheduler async (ADR-0007)
  presentation/    # FastAPI app, composition root, Jinja templates
```

Bağımlılık yönü: `presentation → agent → application → domain`;
`infrastructure` yalnızca composition root'tan instantiate edilir.

## ADR (Architecture Decision Records)

Mimari kararları `docs/decisions/` altında tutuyoruz. Yönetim için
[`adr-kit`](https://github.com/saadettinBerber/adr-kit) Claude Code plugin'i.

### Kurulum (her geliştirici bir kez)

```
/plugin marketplace add saadettinBerber/adr-kit
/plugin install adr-kit@adr-kit
```

### Günlük kullanım

| Komut | Ne yapar |
|-------|----------|
| `/adr-kit:adr-new <başlık>` | Yeni ADR dosyası, otomatik numara, index'e satır |
| `/adr-kit:adr-install-claude-md` | CLAUDE.md'ye ADR disiplin bloğu |

`architecture-decision` skill'i, mimari konular konuşulduğunda otomatik
tetiklenir ve mevcut ADR'ları cevaba katar.

### Mevcut ADR'lar

Tüm aktif kararlar: [`docs/index.md`](docs/index.md).
