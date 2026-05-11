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
