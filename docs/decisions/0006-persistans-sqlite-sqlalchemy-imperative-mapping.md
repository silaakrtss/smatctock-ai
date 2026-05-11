# ADR 0006: persistans-sqlite-sqlalchemy-imperative-mapping

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** Persistans katmanı **SQLite + `aiosqlite` async sürücü +
> SQLAlchemy 2.0 (async)** üzerine kurulur. Domain entity'leri saf
> `dataclass`'tır; SQLAlchemy ORM'e **imperative mapping** ile
> `src/infrastructure/db/mappings.py`'de bağlanır (domain dosyaları
> SQLAlchemy import etmez). Migration yönetimi **Alembic minimal**
> (initial schema + bir örnek migration) ile yapılır. Repository arayüzü
> **hibrittir**: temel CRUD + iş-anlamlı query metodları
> (`list_products_below_threshold`, `list_orders_pending_today` gibi).
>
> **Kapsam:** Tüm kalıcı veri erişimi — ürün, sipariş, sipariş durumu geçmişi,
> kargo, stok eşik tanımı, bildirim kayıtları. `src/infrastructure/db/` ve
> `src/application/ports/*_repository.py` bu ADR'ın somut karşılığıdır.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **Domain dataclass'ları SQLAlchemy import edemez.** `src/domain/`
>   içinde `sqlalchemy.*`, `aiosqlite.*` veya ORM ile ilgili herhangi bir
>   sembol bulunamaz. Mapping `src/infrastructure/db/mappings.py`'de
>   `registry.map_imperatively(DomainClass, table)` ile yapılır.
> - **SQLModel kullanılmaz.** SQLModel SQLAlchemy + Pydantic hibridi;
>   domain'i Pydantic'e bağlayarak ADR-0003'ün "Pydantic domain'de yasak"
>   kuralını ihlal eder.
> - **Application katmanı yalnızca port arayüzlerini görür.** Repository
>   concrete sınıfları (`SqlAlchemyProductRepository` vb.) yalnızca
>   `src/infrastructure/db/` içinde yaşar ve composition root'tan DI ile
>   bağlanır.
> - **Tüm DB I/O async'tir.** Sync session yasak; FastAPI ve agent loop'unun
>   bloklanmaması için tek pipeline async kalır.
> - **Repository'den `Session`/`Engine` sızmaz.** Repository metodları
>   domain dataclass'larını veya basit dataclass DTO'larını döner;
>   `Result`, `Row`, `Session`, `Engine` türleri repository sınırını geçemez.
> - **Migration yönetimi Alembic'tendir.** Production'da `create_all`
>   kullanmak yasak; sadece test fixture'larında izinli.

## Context

ADR-0001 beş tema, ADR-0002 layered + agent mimarisi, ADR-0003 yığın, ADR-0004
LangChain yok, ADR-0005 MiniMax+Gemini sağlayıcıları seçildikten sonra somut
veriye sıra geldi. Mevcut durum:

- `main.py`'da `products` ve `orders` Python list olarak in-memory; restart'ta
  veri kayboluyor.
- "Geçmiş sipariş", "düşük stoklu ürünler", "bugün teslim edilecekler" gibi
  ADR-0001'in iddia ettiği temalar **kalıcı veri + sorgu yeteneği** gerektiriyor.
- Tema 4 (eşik altı stok) ve Tema 5 (sabah özet) scheduler tetiklemeleri DB
  sorgusu üzerinden çalışacak.
- ADR-0001 Open item'ı: 3 günlük, ~30 siparişlik seed data.

Kısıtlar:

1. **Kişisel kurulum maliyeti yok** — postgres / docker isteyen seçenekler
   hackathon süresini yer.
2. **Domain saf kalmalı** — ADR-0002 ve ADR-0003 kuralları.
3. **Test edilebilirlik** — application katmanı DB'siz, fake repository ile
   test edilebilir olmalı (ADR-0002 test stratejisi).
4. **Async pipeline** — FastAPI, agent, LLM SDK hepsi async; DB de async
   olmalı, yoksa thread pool ile sync session sıçraması karmaşıklığa neden
   olur.
5. **Hackathon ölçeği** — eşzamanlı yazar sayısı 1, okuyucu sayısı düşük.
   SQLite'ın tek yazıcı kısıtı pratikte sorun değil.

## Decision

### 1. DB motoru: SQLite + aiosqlite

- Dosya: `data/app.db` (dev), `:memory:` (test).
- Sürücü: `aiosqlite`.
- WAL mode `journal_mode=WAL` açılır (okuyucu eşzamanlılığı için).
- `foreign_keys=ON` pragma her bağlantıda set edilir.

### 2. ORM: SQLAlchemy 2.0 (async)

- `sqlalchemy[asyncio]` + `aiosqlite`.
- `AsyncEngine` + `async_sessionmaker` → composition root'ta tek engine
  yaratılır, session'lar request scope'ta (`Depends` ile) açılır.
- ORM **imperative mapping** ile bağlanır; declarative `Base` veya
  `Mapped[...]` sınıf attribute'ları kullanılmaz.

### 3. Domain ↔ ORM ayrımı: Imperative mapping

Klasör yapısı:

```
src/
  domain/
    products/
      product.py            # @dataclass class Product — SAF, SQLAlchemy import yok
    orders/
      order.py              # @dataclass class Order
      order_status.py       # Enum
    shipping/
      shipment.py
    stock/
      stock_threshold.py
  infrastructure/
    db/
      engine.py             # AsyncEngine fabrikası
      session.py            # async_sessionmaker
      tables.py             # SQLAlchemy Table tanımları (Core)
      mappings.py           # registry.map_imperatively(Domain, Table)
      repositories/
        product_repository.py     # SqlAlchemyProductRepository
        order_repository.py
        shipping_repository.py
      seed.py               # Dev seed data
      migrations/           # Alembic
        env.py
        versions/
          0001_initial_schema.py
```

`tables.py` örneği:

```python
from sqlalchemy import Table, Column, Integer, String, MetaData

metadata = MetaData()

products_table = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("stock", Integer, nullable=False),
)
```

`mappings.py` örneği:

```python
from sqlalchemy.orm import registry
from src.domain.products.product import Product
from src.infrastructure.db.tables import products_table

mapper_registry = registry()


def configure_mappings() -> None:
    mapper_registry.map_imperatively(Product, products_table)
```

Domain `Product` dosyasında SQLAlchemy hiçbir izi yok — saf dataclass,
yalnızca domain method'ları (`is_below_threshold`, `apply_reservation`).

### 4. Migration: Alembic minimal

- `alembic init src/infrastructure/db/migrations` ile başlat.
- `env.py` `metadata` referansı `src/infrastructure/db/tables.py`'a bağlanır.
- İlk migration (`0001_initial_schema.py`) tüm tabloları yaratır.
- En az **bir örnek değişiklik migration'ı** yazılır (örn. `stock_thresholds`
  tablosuna `last_alerted_at` kolonu) — disiplini gösterimi için.
- Production / dev başlatma akışında `alembic upgrade head` çağrılır.
- **Test'lerde** `metadata.create_all()` ile fresh schema kabul edilir
  (Alembic test maliyeti hackathonda gereksiz).

### 5. Repository arayüzü: Hibrit

`application/ports/product_repository.py`:

```python
from abc import ABC, abstractmethod
from src.domain.products.product import Product


class ProductRepository(ABC):
    @abstractmethod
    async def get_by_id(self, product_id: int) -> Product | None: ...

    @abstractmethod
    async def save(self, product: Product) -> None: ...

    @abstractmethod
    async def list_all(self) -> list[Product]: ...

    @abstractmethod
    async def list_below_threshold(self) -> list[Product]: ...
```

Kurallar:

- Temel CRUD: `get_by_id`, `save`, `delete`, `list_all`.
- İş-anlamlı query metodları (Tema 1, 2, 3, 4, 5 ihtiyaçlarına göre):
  `list_orders_pending_today`, `list_products_below_threshold`,
  `list_shipments_delayed`, `find_order_with_history(order_id)` gibi.
- Specification pattern kullanılmaz (overkill).
- Pagination: ilk implementasyonda yok; ihtiyaç doğarsa eklenir.
- Filtre parametreleri açık tipli (örn. `status: OrderStatus`); dict/kwargs
  bag yasak.

### 6. Async / sync sınırı

- Tüm port metodları `async def`.
- Adapter implementasyonları `AsyncSession` kullanır.
- Composition root'ta tek `AsyncEngine`, session per-request (FastAPI
  `Depends`).
- Sync session, sync engine, `Session` import'u **yasak**.

### 7. Seed data

- Dosya: `src/infrastructure/db/seed.py`.
- Format: Python dict listeleri (basit, görünür, IDE-friendly).
- Kapsam:
  - 5-8 ürün (sebze/kooperatif domain'i; mevcut Domates/Salatalık/Patates
    + ek).
  - **~30 sipariş**, **son 3 güne** yayılmış, çeşitli durumlarda
    (`Hazırlanıyor`, `Kargoda`, `Teslim edildi`, `Gecikme`).
  - Her sipariş için status geçmişi (en az 2-3 satır).
  - Bazı kargolar için "delayed" flag'i (Tema 3 senaryosu için).
  - Bazı ürünler için eşik altı stok (Tema 4 senaryosu için).
- Dev başlatma akışında otomatik çalışır (`if settings.env == "dev" and
  db_is_empty(): seed()`).
- Test'lerde seed çağrılmaz; her test kendi fixture'unu kurar.

### 8. Test stratejisi (ADR-0002 ile uyumlu somutlaşma)

- **Fake repository**: `tests/_fakes/in_memory_product_repository.py` gibi —
  port arayüzünü implement eden, dict tabanlı. Application birim testlerinde
  bu kullanılır.
- **Entegrasyon testi (infrastructure/db)**: `aiosqlite:///:memory:` ile
  fresh schema; her test izole DB. `pytest-asyncio` async fixture'lar.
- **E2E (presentation)**: FastAPI `TestClient` + override edilmiş DI; DB ya
  in-memory SQLite ya da tmp dosya.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **PostgreSQL** | Production-ready; ancak docker/postgres kurulumu hackathon süresinden alır. Tek yazıcı kısıtı bizim ölçek için anlamsız. Post-hackathon kararı olabilir (yeni ADR). |
| **DuckDB** | Analitik için iyi; transactional / kalıcı OLTP iş yükü için tasarlanmadı. Tema 4 stok güncellemeleri ve sipariş yazımı için uygun değil. |
| **Tek model (SQLAlchemy = domain)** | Hızlı yazılır ama ADR-0002 "domain saf" kuralını ihlal eder. ORM tipleri (`Mapped`, `relationship`) domain'e sızar; test edilebilirlik bozulur. |
| **Declarative mapping + ayrı domain dataclass + mapper** | Tek model ile imperative mapping arası bir orta yol; ama declarative `Base`'in import edilmesi domain'in sızma ihtimalini açar. Imperative mapping daha temiz çünkü domain'in `__init__` ve attribute'ları üzerinde kontrol bizdedir. |
| **SQLModel** | SQLAlchemy + Pydantic hibridi; Pydantic'i domain'e dayatır. ADR-0003'ün "Pydantic domain'de yasak" kuralıyla doğrudan çelişir. SQLModel'in pratik avantajları (tek model) ADR'larımızla uyumsuz. |
| **Peewee** | Daha basit ORM; async desteği zayıf, ekosistem küçük, alembic eşdeğeri sınırlı. Modern Python projeleri için SQLAlchemy 2.0 fiili standart. |
| **Raw SQL (`aiosqlite` üstünde direkt)** | Tam kontrol; ancak query oluşturma, model bağlama, migration el yazısı yük getirir. Hackathon süresinde net kayıp. |
| **`create_all` only (Alembic yok)** | Hackathon pragmatiği olabilirdi; ancak "büyük proje gibi disiplinli" kullanıcı tercihi ve ADR-0002'nin disiplin vurgusu Alembic'i minimum gereklilik yapar. Minimal Alembic 30 dakikadan az maliyet, disiplin gösterimi yüksek. |
| **Manuel SQL DDL dosyaları (`init.sql`)** | ORM şemadan ayrı tek source-of-truth ister; her şema değişikliği iki yerde elle güncellenir. Hata yüzeyi büyük. |
| **Specification pattern** | Query nesneleştirmesi; hackathon kapsamında 5-6 query var, nesneleştirme overkill. Hibrit repository yeterli. |
| **İnce CRUD repository + ayrı QueryService** | Daha temiz ayrım; ama her domain için iki sınıf demek (Repository + QueryService) — dosya sayısı şişer, fayda marjinal. |

## Consequences

### Olumlu

- **Domain tamamen saf** — SQLAlchemy değiştirilebilir, başka bir DB'ye
  geçilebilir, hatta DB tamamen kaldırılabilir; domain'e dokunulmaz.
- **Application testleri DB'siz çalışır** — fake repository ile hızlı,
  deterministik, paralel test. ADR-0002 test stratejisi sorunsuz çalışır.
- **Hibrit repository** Tema 1-5'in ihtiyaçlarını net karşılar; chatbot
  agent'ı "düşük stoklu ürünler" gibi soruları tek metod çağrısı ile alır.
- **SQLite + WAL** hackathon ölçeğinde fazlasıyla yeterli; sıfır kurulum
  maliyeti.
- **Alembic minimal** disiplin gösterimi sağlar; jüri "migration disiplini
  var mı?" diye sorarsa cevabımız net.
- **Tüm pipeline async** → FastAPI + LLM SDK + DB hepsi tek dünya; agent
  loop bloklanmaz.

### Olumsuz

- **Imperative mapping boilerplate'i** var: `tables.py`, `mappings.py`,
  `configure_mappings()` çağrısı composition root'ta. Karşılığında: domain
  sızıntısı sıfır, refactor güvenli.
- **Alembic kurulumu** hackathon başlangıcında 15-30 dakika alır; bu
  zamanın faturasını ilk gün ödüyoruz.
- **SQLAlchemy 2.0 async API** tip annotation'larında bazen sürtünme yaratır
  (`AsyncSession`'ın metodları kafa karıştırıcı dönüş tipleri verebilir);
  mypy strict modda fazladan tip-yardımcı yazmak gerekebilir.
- **SQLite tek yazıcı kısıtı** — eğer demo sırasında paralel scheduler
  + agent + sabah job aynı anda yazarsa kuyruk birikebilir. Hackathon
  ölçeğinde sorun değil ama post-hackathon production senaryosunda
  PostgreSQL'e geçiş gerekir.
- **Seed data senkronizasyonu** — domain şeması değişirse seed.py de
  güncellenmek zorunda; CI test'i seed'i yükleyerek bunu doğrular.

## Open items

- [ ] `pyproject.toml` bağımlılıkları: `sqlalchemy[asyncio]>=2.0,<3`,
      `aiosqlite>=0.20`, `alembic>=1.13`.
- [ ] `src/infrastructure/db/engine.py` — `AsyncEngine` fabrikası, WAL +
      foreign_keys pragma'larını set eden event listener.
- [ ] `src/infrastructure/db/session.py` — `async_sessionmaker`.
- [ ] `src/infrastructure/db/tables.py` — Product, Order, OrderStatusHistory,
      Shipment, StockThreshold, NotificationLog tabloları (Core, Table API).
- [ ] `src/infrastructure/db/mappings.py` — `configure_mappings()`.
- [ ] `src/domain/*/` — saf dataclass domain entity'leri.
- [ ] `src/application/ports/*_repository.py` — port arayüzleri (hibrit
      CRUD + iş-anlamlı query metodları).
- [ ] `src/infrastructure/db/repositories/` — SqlAlchemy implementasyonları.
- [ ] `src/infrastructure/db/seed.py` — 5-8 ürün, ~30 sipariş, 3 günlük
      dağılım, çeşitli kargo durumları.
- [ ] Alembic kurulumu: `alembic init`, `env.py` metadata bağlama,
      `0001_initial_schema.py` migration.
- [ ] Test fakes: `tests/_fakes/in_memory_*_repository.py`.
- [ ] Entegrasyon testleri: her repository için en az 1 happy path + 1 edge
      case (`tests/integration/db/`).
- [ ] FastAPI `Depends` ile per-request session açma/kapama; composition
      root'ta engine'ı app lifespan'a bağlama.
- [ ] CI'da `alembic upgrade head` smoke testi (migration dosyalarının
      tutarlılığını doğrular).

## Affected areas

- `src/domain/` — saf dataclass entity'ler bu ADR ile yaratılır.
- `src/application/ports/` — repository arayüzleri.
- `src/infrastructure/db/` — engine, session, tables, mappings, repositories,
  seed, Alembic migrations.
- `src/presentation/main.py` — composition root, engine lifespan, DI
  binding.
- `pyproject.toml` — SQLAlchemy, aiosqlite, alembic bağımlılıkları.
- `main.py` (kök) — bu ADR ile parçalanır; in-memory `products`/`orders`
  listeleri kaldırılır.
- [[0002-mimari-yaklasim-layered-agent]] — bu ADR oradaki
  `infrastructure/db/` katmanının somut implementasyonudur.
- [[0003-cerceve-teknoloji-yigini]] — bu ADR oradaki yığına SQLAlchemy,
  aiosqlite, alembic ekler.
- _gelecek ADR_ — Scheduler (ADR-0007) bu DB üzerinde tetikleme yapacak;
  agent tool'ları (ADR-0010?) bu repository'leri kullanacak.
