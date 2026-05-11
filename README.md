# SmartStock AI — Kurulum

Projeyi yerel ortamda ayağa kaldırma adımları.

## Gereksinimler

- Python 3.10+
- MiniMax API anahtarı

## 1. Repoyu klonla

```bash
git clone https://github.com/silaakrtss/smatctock-ai.git
cd smatctock-ai
```

## 2. Sanal ortam oluştur ve bağımlılıkları yükle

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. `.env` dosyasını hazırla

```bash
cp .env.example .env
```

`.env` içindeki `MINIMAX_API_KEY` değerini kendi anahtarınla doldur.

## 4. Sunucuyu başlat

```bash
uvicorn main:app --reload
```

Tarayıcıdan aç: <http://127.0.0.1:8000>

## 5. ADR (Architecture Decision Records)

Mimari kararları `docs/adr/` altında tutuyoruz. Yönetim için [`adr-kit`](https://github.com/saadettinBerber/adr-kit) Claude Code plugin'ini kullanıyoruz.

### Kurulum (her geliştirici bir kez yapar)

Claude Code içinde:

```
/plugin marketplace add saadettinBerber/adr-kit
/plugin install adr-kit@adr-kit
```

### Günlük kullanım

| Komut | Ne yapar |
|-------|----------|
| `/adr-kit:adr-init` | `docs/` iskeletini ve ilk index'i oluşturur (proje başında bir kez) |
| `/adr-kit:adr-new <başlık>` | Yeni ADR dosyası açar, numarayı otomatik verir, index'e satır ekler |
| `/adr-kit:adr-install-claude-md` | CLAUDE.md'ye ADR disiplin bloğunu ekler |

Ayrıca `architecture-decision` skill'i, mimari konular konuşulduğunda otomatik tetiklenir ve mevcut ADR'ları okuyup cevaba katar.

### Ne zaman ADR yazılır?

Birden fazla modülü etkileyen kararlarda:

- Modül sınırı / paket yapısı değişiklikleri
- DB, cache, queue seçimi
- Auth / yetkilendirme modeli
- API protokolü (REST/gRPC/GraphQL)
- Cross-cutting konular: logging, error handling, observability
- Deployment topolojisi

Tek dosyalık bir bugfix veya yerel refactor için ADR gerekmez — commit mesajı yeter.
