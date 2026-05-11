# docs/

Bu klasör projenin **mimari dokümantasyon** kaynağıdır. Üç tür içerik:

- **`decisions/`** — Architecture Decision Records (ADR). Immutable;
  bir karar değişirse eski ADR `Superseded` olur, yeni ADR yazılır.
- **`concepts/`** — Yaşayan kavram sayfaları. Modül haritası, akış
  şeması, "şu dosya nereye gider" karar akışı gibi referanslar.
  Güncellenebilir.
- **`index.md`** — Tüm ADR'ların ve concept sayfalarının listesi.
  Tek giriş noktası.

## Yeni ADR yazarken

`decisions/0000-template.md` şablonunu kullan.

1. `decisions/` altında **bir sonraki numarayı** bul (NNNN).
2. Şablonu kopyala: `cp 0000-template.md NNNN-kisa-baslik.md`
3. Doldur (özellikle `## TL;DR` bölümü — AI asistan bunu alıntılar).
4. `index.md`'ye satır ekle.
5. Etkilenen `concepts/` sayfalarını güncelle.

## ADR okuma disiplini

Bir ADR'a referans verirken:

- `## TL;DR` bloğunu **birebir alıntıla** — kendi cümlenle özetleme.
- Sınıf/port/modül **isminden anlam çıkarsama** — gerekçe ADR'da.
- "Şu an X, ideal Y" diyorsa **ikisini de söyle**.

Bu disiplin `architecture-decision` skill'i tarafından AI asistanına
zorunlu kılınır. Kurulum için repo kökündeki `INSTALL.md`'ye bak.
