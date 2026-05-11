# ADR 0003: cerceve-teknoloji-yigini

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Proje çerçeve teknoloji yığını şu sabit setten oluşur:
> **FastAPI** (HTTP yüzeyi), **Pydantic v2** (sadece presentation DTO ve config —
> domain'de yasak), **httpx** (HTTP client), **pydantic-settings** (env/config),
> **pytest + pytest-cov + pytest-asyncio + pytest-xdist + freezegun** (test
> stack), **ruff** (lint + format), **mypy --strict** (tip kontrolü) ve
> **import-linter** (katman ihlali kontrolü).
>
> **Kapsam:** Üretim kodunun ve test stack'inin temel kütüphane seçimi. DB
> (ADR-0005), scheduler (ADR-0006) ve LLM agent çerçevesi (ADR-0004) bu ADR'ın
> dışındadır; ayrı kararlarda netleşir.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **Pydantic, `src/domain/` içinde import edilemez.** Domain entity'leri saf
>   `dataclass` ile yazılır; validation kuralları domain method'larında kodlanır.
> - **Pydantic, `src/application/` katmanında DTO/port arayüzü olarak**
>   kullanılmaz; application input/output `dataclass`'tır.
>   Pydantic yalnızca **presentation katmanında** (FastAPI request/response,
>   `Settings` config) ve adapter sınırlarında **dış dünya formatlarını
>   modellemek** için kullanılır.
> - **FastAPI, `src/presentation/` dışında import edilemez.**
> - **httpx, yalnızca `src/infrastructure/` adapter'larında** kullanılır.
> - **Test araçları, üretim kodunda import edilemez** (`pytest`, `freezegun`,
>   vb. yalnızca `tests/` altında).
> - **Yeni bağımlılık eklemek bir ADR konusudur.** Bu listedeki teknolojiler
>   dışında bir paket eklemek isteyen, ya mevcut ADR'ı superseded yapar ya da
>   yeni bir ADR açar.

## Context

ADR-0002 ile katmanlı mimari kabul edildi; her katmanın hangi türden bağımlılık
alabileceği yasaklarla belirlendi (örn. domain saf, application port'ları
tanımlar, presentation composition root). Şimdi bu mimarinin **somut kütüphane
seçimleri** yapılmadan kod yazılamaz.

Mevcut durum:
- `main.py` zaten `FastAPI`, `httpx`, `python-dotenv`, `pydantic` kullanıyor.
- Test stack'i henüz yok; ADR-0002 test stratejisini detaylı tanımladı ama
  somut araçlar yazılı değil.
- Lint/tip/katman doğrulama araçları yok; ADR-0002'de CI Open item olarak
  duruyor.

Acı noktası: Kütüphane kararları sözlü kalırsa "kim hangisini ekledi, neden?"
sorusu altı ay sonra cevapsız kalır. Ayrıca Pydantic'in **nereye kadar** sızması
hakkında net kural yoksa, domain bir gün Pydantic'e bağlanır ve ADR-0002'nin
"domain saf" kuralı sessizce ihlal edilir.

Gereksinim: Tüm çerçeve teknolojiler **tek bir kararda** sabitlenmeli; her birinin
hangi katmanda kullanılabileceği **yasakla** netleştirilmeli; yeni bağımlılık
eklemek bilinçli bir karar (yeni ADR) olmalı.

## Decision

### 1. Üretim bağımlılıkları

| Paket | Sürüm sınırı | Katman | Rolü |
|-------|--------------|--------|------|
| `fastapi` | `>=0.110,<0.120` | `presentation/` | HTTP framework, OpenAPI, DI |
| `uvicorn[standard]` | en güncel kararlı | runtime | ASGI server |
| `pydantic` | `>=2.6,<3` | `presentation/` (DTO, config) | Request/response validation |
| `pydantic-settings` | `>=2.2,<3` | `presentation/config/` | Env-based config (Settings) |
| `httpx` | `>=0.27,<0.30` | `infrastructure/` | HTTP client (LLM, notifier adapter'ları) |
| `python-dotenv` | mevcut | runtime | `.env` yükleme (uvicorn entry'sinde) |

> **Not:** `python-dotenv`, `pydantic-settings`'in altında zaten kullanılıyor;
> direkt import yalnızca uygulama başlatma noktasında (`presentation/main.py`)
> yapılır, başka yerde yasak.

### 2. Geliştirme / test bağımlılıkları

| Paket | Rolü |
|-------|------|
| `pytest` | Test runner |
| `pytest-cov` | Coverage ölçümü (eşik: ADR-0002'deki tablo) |
| `pytest-asyncio` | Async test desteği |
| `pytest-xdist` | Paralel test |
| `freezegun` | Zamanı dondurmak için (FIRST: Repeatable) |
| `httpx` | FastAPI `TestClient`'ın altında (zaten üretimde de var) |
| `ruff` | Lint + format (mevcut `black` + `flake8`'in yerine; tek araç) |
| `mypy` | Tip kontrolü, **strict mode zorunlu** |
| `import-linter` | Katman ihlali kontrolü (CI'da kırılır) |

### 3. Pydantic'in sızıntı sınırı

Pydantic güçlü ama bir **framework**. Domain'i Pydantic'e bağlamak, mimarinin
çekirdek kuralını sessizce ihlal eder. Bu nedenle:

- **`src/domain/`**: Yalnızca `dataclass`, `enum`, `typing`, standart kütüphane.
  Pydantic, FastAPI, SQLAlchemy import yasak.
- **`src/application/`**: Yalnızca `dataclass`, `domain` modülleri, kendi `ports/`
  arayüzleri. Pydantic DTO olarak kullanılamaz.
- **`src/agent/`**: `application/ports/` ve `domain/` import edebilir; Pydantic
  doğrudan kullanılamaz (LLM client portu zaten dataclass dönecek).
- **`src/presentation/`**: Pydantic `BaseModel` request/response DTO'ları,
  `pydantic-settings` `BaseSettings` config sınıfları **burada serbest**.
- **`src/infrastructure/`**: Adapter'lar dış dünya verisini (örn. LLM API JSON,
  kargo API JSON) ayrıştırmak için **kendi sınırı içinde** Pydantic kullanabilir;
  ancak application'a verdiği dönüş tipi her zaman **domain/application
  dataclass'ı** olmalıdır. Pydantic adapter'ın iç meselesi olarak kalır.

Bu kuralın yaptırımı `import-linter` ile CI'da otomatik kontrol edilir.

### 4. CI ve kod kalitesi pipeline'ı

CI'da aşağıdaki kontroller **zorunlu** çalışır; herhangi biri başarısız olursa
build kırılır:

1. `ruff check .` — lint
2. `ruff format --check .` — format
3. `mypy --strict src/` — tip kontrolü
4. `lint-imports` (`import-linter`) — katman ihlali kontrolü
5. `pytest --cov=src --cov-fail-under=85` — test + coverage eşiği (ADR-0002)

### 5. `requirements.txt` → `pyproject.toml` geçişi

Mevcut `requirements.txt` 36 byte; minimal. Bu ADR ile birlikte:

- `pyproject.toml` oluşturulur.
- Üretim ve dev bağımlılıkları ayrılır (`[project.dependencies]` ve
  `[project.optional-dependencies.dev]`).
- `requirements.txt` silinir veya CI'da `pip-compile` ile lock dosyası olarak
  yeniden üretilir.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **Flask + manuel validation** | Async desteği zayıf, Pydantic entegrasyonu manuel, OpenAPI yok. FastAPI'nin sağladığı her şeyi yeniden inşa etmek gerekirdi. |
| **Litestar** | Modern ve hızlı; ancak topluluk daha küçük, FastAPI'nin ekosistem zenginliği yok. Hackathonda sürpriz riski. |
| **Pydantic'i domain'de de serbest bırakmak** | Domain'in "framework yok" kuralı sessizce ihlal edilir; bir gün domain'i başka bir bağlama taşımak imkansızlaşır. Test edilebilirlik de zarar görür çünkü Pydantic validation'ı işin içine girer. |
| **`black` + `flake8` + `isort` ayrı ayrı** | Ruff bu üçünün hızlı + tek paketli halefi; CI süresini ve config'i azaltır. |
| **`pylint` (mypy yerine)** | Pylint statik analiz, mypy tip kontrolü — farklı işler. Tip güvenliği için mypy zorunlu; pylint'in lint yönü zaten ruff'ta var. |
| **`requirements.txt` ile devam** | Modern Python projeleri `pyproject.toml` standardına geçti; üretim/dev ayrımı, build sistemi metadata'sı, tool config'i tek dosyada toplanır. |
| **`pydantic-settings` yerine düz `os.environ`** | Tip güvenliği yok, validation yok, eksik env'i geç fark ederiz. `pydantic-settings` küçük ek maliyet, büyük güvenlik kazancı. |

## Consequences

### Olumlu

- Her kütüphanenin **hangi katmanda yaşadığı yazılı**; "Pydantic'i domain'e
  koyalım mı?" tartışması bir daha açılmaz.
- CI pipeline'ı bu ADR ile somutlaşır; ruff/mypy/import-linter/coverage hep
  birlikte kalite duvarı kurar.
- `pyproject.toml` standardı ile üretim/dev bağımlılıkları temiz ayrılır;
  hackathon sonrası proje yaşamaya devam ederse modern toolchain hazır olur.
- Pydantic'in adapter sınırında kullanılabilmesi, dış API JSON'larını
  ayrıştırırken güç sağlar; ama bu kullanımın sızdırılmaması yazılı.

### Olumsuz

- İlk kurulum maliyeti yüksek: `pyproject.toml`, `ruff` config, `mypy` strict
  ayarları, `import-linter` kontrat dosyası — hepsi bu ADR'la birlikte
  yazılacak. İlk gün hızı düşer; sonraki günler hızlanır.
- `mypy --strict` Python'da yazmaya alışkın olmayan biri için ilk başta
  sürtünme yaratır; karşılığında tip ile yakalanan hatalar çok değerlidir.
- Pydantic'i domain'de yasaklamak, küçük projelerde "validation tekrarı"
  hissi yaratabilir; ama domain validation'ı **iş kuralı**dır, Pydantic
  validation'ı **şema kuralı**dır — ikisi aynı şey değil.

## Open items

- [ ] `pyproject.toml` yaz: `[project]`, `[project.dependencies]`,
      `[project.optional-dependencies.dev]`, `[tool.ruff]`, `[tool.mypy]`,
      `[tool.pytest.ini_options]`.
- [ ] `importlinter` config dosyası (`.importlinter`) yaz; katman kontratları:
      `domain` → hiçbir şeye bağlı değil; `application` → yalnızca `domain` +
      kendi `ports/`; `agent` → `application` + `domain`; `infrastructure` →
      `application/ports` + `domain`; `presentation` → composition root.
- [ ] `mypy.ini` veya `pyproject.toml` `[tool.mypy]` strict ayarları.
- [ ] CI workflow dosyası (`.github/workflows/ci.yml` veya eşdeğeri).
- [ ] `requirements.txt`'yi sil, `pyproject.toml`'a geçir.
- [ ] `.env.example`'ı `pydantic-settings` `Settings` sınıfıyla hizala.

## Affected areas

- `pyproject.toml` — bu ADR ile yaratılacak; üretim ve dev bağımlılıklar burada.
- `requirements.txt` — silinecek (veya lock dosyasına dönüşecek).
- `src/presentation/config/` — `Settings` sınıfı burada doğacak.
- CI pipeline — bu ADR'ın somutlaşması.
- [[0002-mimari-yaklasim-layered-agent]] — bu ADR oradaki katman kurallarının
  somut kütüphane karşılığıdır.
- _gelecek ADR'lar_ — ADR-0004 (LLM agent çerçevesi), ADR-0005 (DB), ADR-0006
  (scheduler) bu yığına eklenecek.
