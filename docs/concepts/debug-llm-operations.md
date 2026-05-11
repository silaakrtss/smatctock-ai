# Debug: LLM Operasyonları

Bu sayfa LLM sağlayıcı çağrılarında, agent loop'unda ve tool calling
akışında karşılaşılan sorunları toplar.

İlgili ADR'lar:
- [ADR-0005 LLM sağlayıcı — MiniMax + Gemini](../decisions/0005-llm-saglayici-secimi-minimax-gemini.md)
- [ADR-0009 Agent loop — basit tool-calling](../decisions/0009-agent-loop-tool-calling.md)

---

## LLM kotası doldu — HTTP 503

**Sebep:** Sağlayıcı rate limit verdi. Adapter 3 deneme exponential
backoff yapıp `LLMRateLimitError` fırlattı; presentation katmanı
bunu HTTP 503'e çevirdi.

**Çözüm:**

1. **Geçici:** Birkaç dakika bekle ve tekrar dene.
2. **Sağlayıcı değiştir:** `.env`'de `LLM_PROVIDER=gemini` (Gemini free
   tier cömerttir: dakikada ~15, günde ~1500 istek). Sunucuyu yeniden
   başlat.

ADR-0005 § 3 emrediyor: **otomatik runtime fallback yok**. Sağlayıcı
seçimi statik — env değiştirip restart şart.

---

## "İsteğinizi tam çözemedim, biraz daha spesifik sorabilir misiniz?" — HTTP 422

**Sebep:** Agent loop max 8 iterasyon limitine takıldı
(`AgentLoopExceededError`). Model her turda tool çağırdı ama nihai
cevaba ulaşamadı.

**Çözüm:**

1. **Kullanıcıya:** Soruyu daha spesifik sor ("Domates için" gibi
   somut ad ekle, sipariş numarası ver).
2. **Geliştiriciye:** `logs_llm/<bugün>.jsonl` dosyasını incele —
   8 turun her birinde hangi tool'un hangi argümanla çağrıldığını,
   ne döndürdüğünü gör. Genelde tool argümanlarındaki yanlış parse
   veya domain entity'nin bulunamaması döngüye sokar.

Limit `AGENT_MAX_TOOL_ITERATIONS` env değişkeniyle artırılabilir
(dev'de debug için), ama ADR-0009 § 2 üretim default'unu 8 sabitler.

---

## LLM çağrı geçmişini incele

**Senaryo:** Agent neden yanlış tool çağırdı? Hangi argümanlar gitti?
Model ne döndürdü?

**Çözüm:** `logs_llm/YYYY-MM-DD.jsonl` dosyaları her LLM çağrısının
request mesajları + response (content + tool_calls + reasoning_details)
JSONL satırlarını içerir. ADR-0005 § 5'in `reasoning_details` korunma
kuralının da kanıtıdır — bu loglarda M2.7'nin reasoning chain'i
görülebilir.

**Format örneği:**

```jsonl
{"timestamp":"2026-05-11T15:14:48.894","provider":"minimax","model":"MiniMax-M2.7","request":[...],"response":{"content":"...","tool_calls":[...],"reasoning_details":{...}}}
```

`.gitignore`'da olduğu için commit edilmez. `make clean` veya manuel
silebilirsin; otomatik rotasyon yok (hackathon ölçeği).

İnceleme için pratik:

```bash
cat logs_llm/2026-05-11.jsonl | jq '.response.tool_calls'
cat logs_llm/2026-05-11.jsonl | jq 'select(.response.content | tostring | contains("<think>"))'
```

---

## "LLM servisine ulaşılamadı" — HTTP 503

**Sebep:** Adapter 3 deneme sonrası `LLMTransportError` (timeout,
bağlantı reddi, DNS) fırlattı.

**Çözüm:**

1. **Ağ bağlantısını kontrol:** `curl -I https://api.minimax.io/v1` veya
   `curl -I https://generativelanguage.googleapis.com/`
2. **API key geçerli mi:** Sağlayıcı paneline gir, key revoke edilmiş
   olabilir.
3. **Diğer sağlayıcıyı dene:** `LLM_PROVIDER` değiştir.

---

## `<think>...</think>` bloğu yanıtta görünüyor

**Sebep:** MiniMax M2.7 reasoning model; bazen final content'inde
düşünce bloğunu açıkça döndürür. Bu sürümde
`strip_reasoning_blocks` sanitizer UI'a giderken temizler.

**Eğer hala görüyorsan:**

1. **Tarayıcı cache:** Eski JS yüklenmiş olabilir. `Ctrl+Shift+R`
   ile sert yenileme.
2. **Sürüm:** `git log --oneline | grep think` ile fix commit'inin
   merge edildiğini doğrula (`e7dbd0e` veya sonrası).

**Önemli mimari not:** Sanitizer YALNIZCA `AiChatResponse`'a giderken
çalışır. Conversation state'inde (`Conversation` sınıfı) reasoning
blokları TAM korunur — ADR-0005 § 5 (M2.7 multi-turn caveat'i) ve
ADR-0009 § 2 emrediyor. Bu kuralı sanitizer'a taşımak yasak.

---

## Tool yürütme hatası: `Bilinmeyen tool: X`

**Sebep:** Model registry'de olmayan bir tool çağırdı.

**Çözüm:**

1. **Hata bekleniyor:** Model uydurma tool denedi; dispatcher
   `ToolResult.error` döndü, agent loop bunu modele geri verdi ve
   modelin yeni bir denemeye geçmesini sağladı. Bu **normal**.
2. **Sıkıntı varsa:** Sistem prompt'unu ya da tool tanımlarını
   netleştir. `src/agent/tools/definitions.py`'deki açıklamalar
   "ne zaman kullan" bilgisi içermeli.
