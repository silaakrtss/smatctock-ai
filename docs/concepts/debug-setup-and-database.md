# Debug: Kurulum ve Veritabanı

Bu sayfa kurulum sürecinde ve veritabanı kullanımında karşılaşılan
sorunları toplar. Yeni sorun çıktığında kaynağı veritabanı, migration
veya seed ile ilgiliyse buraya ekle.

İlgili ADR: [ADR-0006 Persistans — SQLite + SQLAlchemy async](../decisions/0006-persistans-sqlite-sqlalchemy-imperative-mapping.md).

---

## `OperationalError: no such table: products`

**Sebep:** `make migrate` çalıştırılmamış, Alembic henüz initial şemayı
uygulamamış. `data/app.db` dosyası ya hiç yok ya da boş.

**Çözüm:**

```bash
make migrate    # alembic upgrade head, data/ klasörü dahil
make seed       # dev seed (3 ürün + 3 sipariş + 1 kargo)
```

Veya tek komutla:

```bash
make bootstrap  # install + migrate + seed
```

---

## "Boş dashboard, hiç ürün yok"

**Sebep:** Migration başarılı ama seed atlanmış. DB ayağa kalktı ancak
hiç satır eklenmedi.

**Çözüm:** `make seed` — `src.infrastructure.db.seed_cli` Settings'ten
DATABASE_URL okur, mapping'leri yükler, `seed_dev_data` çağırır
(ADR-0006 § 5: seed yalnızca dev/test için, production'da çağrılmaz).

---

## Demo'yu sıfırdan başlatmak istiyorum

**Senaryo:** Provada notification'lar birikti, taze bir slate'le yeniden
başlamak istiyorsun.

**Çözüm:**

```bash
make reset-db   # data/app.db'yi sil → migrate → seed
```

Bu komut idempotent; istediğin kadar çağırabilirsin.

---

## `make install` global Python'u kirletti

**Sebep:** Sanal ortam aktive edilmeden `make install` çalıştırıldı.
Pip dev bağımlılıklarını global'e yazdı.

**Çözüm:**

```bash
python3 -m venv .venv
source .venv/bin/activate          # prompt'ta (.venv) görünmeli
make install
```

Eğer global'i temizlemek istiyorsan: `pip list --user` ile yüklü
paketleri gör, gereksizleri `pip uninstall <paket>` ile kaldır.

---

## Alembic migration history bozuldu

**Sebep:** `alembic_version` tablosu DB'de var ama migration dosyası
yok veya çakışıyor.

**Çözüm:** Hackathon ölçeğinde DB'yi sıfırlamak en hızlı yol:

```bash
make reset-db
```

Üretim ortamında: önce mevcut migration history'sini inceleyip
`alembic stamp <revision>` ile manuel düzelt. Hackathon kapsamı için
bu yol gerekmiyor.

---

## SQLite dosyası kilitli (Database is locked)

**Sebep:** Aynı anda iki süreç DB'yi yazmaya çalışıyor (örn. uvicorn
çalışırken `make seed` koşuldu).

**Çözüm:**

1. `make run`'ın çalıştığı terminali kapat (`Ctrl+C`)
2. `ps aux | grep uvicorn` ile artık process kaldıysa `kill -9 <pid>`
3. Komutu tekrar dene

WAL modu açık olduğu için (`PRAGMA journal_mode=WAL`, ADR-0006 § 1)
okuyucular bloklanmaz; ama yazıcılar tek seferde bir tane çalışır.
