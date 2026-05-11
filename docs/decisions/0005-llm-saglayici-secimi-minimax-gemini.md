# ADR 0005: llm-saglayici-secimi-minimax-gemini

- Status: Accepted
- Date: 2026-05-11
- Supersedes: -
- Superseded-by: -

## TL;DR (özet istendiğinde bunu alıntıla)

> **Karar:** LLM sağlayıcı olarak **MiniMax M2.7 birincil**, **Google Gemini
> Flash (2.0 veya 2.5) fallback** seçilir. İkisi de **sıfır/çok düşük maliyetli**
> seçeneklerdir. Hangi adapter'ın aktif olacağını `LLM_PROVIDER` env değişkeni
> belirler (`minimax` veya `gemini`); composition root'ta DI ile bağlanır.
>
> **Kapsam:** `src/infrastructure/llm/` altındaki tüm adapter'lar ve
> `application/ports/llm_client.py` port'unun somut implementasyonları. Üst
> katmanlar (`agent`, `application`, `domain`, `presentation`) bu karardan
> habersizdir.
>
> **Önemli kısıtlar (kesin yasak — istisnasız):**
> - **MiniMax adapter'ı `openai` Python SDK'sı ile yazılır**, base URL
>   `https://api.minimax.io/v1` olarak override edilir. Mevcut `httpx`-tabanlı
>   direkt HTTP kodu bu ADR ile **terk edilir**; M2.7'nin OpenAI uyumlu
>   endpoint'i resmi yoldur.
> - **Conversation state, modelin tam yanıtını saklar** — reasoning/thinking
>   blokları, `reasoning_details`, `<think>` tag'leri, tool_calls ve text
>   içeriklerinin **hiçbiri truncate edilemez**. Bu, M2.7'nin resmi
>   dokümantasyonunda multi-turn tool calling için **şart** koşulmuş kuraldır;
>   ihlal edildiğinde sonraki turlarda tool reasoning kırılır.
> - **Sağlayıcıya özel sınıflar `infrastructure/llm/` dışında import edilemez.**
>   Üst katmanlar yalnızca `application/ports/llm_client.py`'deki port arayüzünü
>   görür.
> - **Conversation state'in serileştirilmesi sağlayıcıya özel detayları
>   gizler.** Port dataclass'ları (`Message`, `ToolCall`, `LLMResponse`)
>   sağlayıcı-bağımsız tasarlanır; adapter, sağlayıcının ham formatından bu
>   dataclass'lara çevrim sorumluluğunu üstlenir.
> - **Sağlayıcı değiştirmek bir adapter işidir.** Yeni sağlayıcı eklemek,
>   `infrastructure/llm/<saglayici>_client.py` dosyası yazmak, `Settings`'e
>   env değişkenleri eklemek ve composition root'ta DI binding'ini eklemekten
>   ibarettir. Bu ADR superseded yapılmaz; ek sağlayıcılar **bu ADR'ı genişletir**.

## Context

ADR-0001 beş tema iddiası, ADR-0002 layered + ayrı agent katmanı, ADR-0003
çerçeve yığını, ADR-0004 LangChain/LangGraph yasağı + agent katmanını kendimiz
yazma kararı verildikten sonra sıra **somut LLM sağlayıcı** seçimine geldi.

Kısıtlar:

1. **Kişisel bütçe yok** — ücretli sağlayıcılar (Anthropic Claude, OpenAI)
   öncelikli değil. Free tier veya çok ucuz fiyatlandırma şart.
2. **Tool calling kalitesi tüm projenin omurgası** — ADR-0002 ve ADR-0004
   agent katmanını tool calling üzerine kurdu. Sağlayıcının tool calling'i
   güvenilir olmalı.
3. **Türkçe yeterli olmalı** — kullanıcı kitlesi Türkçe konuşuyor. Mevcut
   sistem promptu zaten Türkçe; sağlayıcı bunu desteklemeli.
4. **Mevcut yatırımı yok etmemek** — `main.py`'da MiniMax kodu zaten var.
5. **ADR-0002'nin port/adapter mimarisi**, yeni sağlayıcı eklemeyi neredeyse
   bedavaya getiriyor. Bu, **çoklu sağlayıcı stratejisini** uygulanabilir
   kılıyor — primary + fallback (veya kıyaslama) mimari iddiayı güçlendirir.

Araştırma bulguları (2026-05-11 itibariyle):

- **MiniMax M2.7** (2026-03-18 çıkışlı):
  - ~230B MoE, 10B aktif parametre; Tier-1 sınıfında en küçük aktif ayak izi.
  - Fiyat: $0.30 input / $1.20 output per million tokens (Claude Opus 4.6'dan
    ~50x ucuz input tarafı).
  - **Tool calling benchmark'ları güçlü**: BFCL multi-turn'de M2.5'te 76.8
    (sektör lideri), Toolathon'da 46.3% (küresel top tier), MM Claw'da 40
    karmaşık skill'de %97 uyum.
  - **OpenAI uyumlu endpoint** (`https://api.minimax.io/v1`) ve Anthropic
    uyumlu endpoint (`https://api.minimax.io/anthropic`) destekli — XML tag
    parsing yalnızca yerel inference (vLLM/SGLang) içindir.
  - Parallel tool calling destekli.
  - **Kritik caveat**: resmi dokümantasyon "multi-turn conversation'da modelin
    tam yanıtı (reasoning, thinking, tool_use blokları dahil) mesaj geçmişine
    eklenmelidir; truncate etmek reasoning chain'i kırar" diyor.

- **Google Gemini Flash 2.0 / 2.5**:
  - **Cömert free tier** (Google AI Studio API key kredi kartı istemiyor).
  - Function calling olgun, parallel calls destekli.
  - 1M context window — uzun konuşma ve büyük tool sonuçları için sigorta.
  - Resmi `google-genai` Python SDK olgun ve async.
  - Türkçe doğal (Google çoklu dil yatırımı güçlü).

Önceki ön-okumam (MiniMax tool calling zayıf olabilir) **araştırmayla
çürütüldü**. M2.7 tool calling açısından modern Tier-1 modellere yakın
performans sergiliyor.

## Decision

### 1. Birincil sağlayıcı: MiniMax M2.7

- Adapter: `src/infrastructure/llm/minimax_client.py`.
- Implementasyon: **`openai` Python SDK'sı**, `base_url="https://api.minimax.io/v1"`,
  `api_key=settings.minimax_api_key`.
- Model: `MiniMax-M2.7` (env'de override edilebilir).
- Mevcut `httpx` ile yazılmış MiniMax çağrı kodu bu ADR ile **kaldırılır** ve
  yeni adapter yazılır.

### 2. Fallback sağlayıcı: Google Gemini Flash

- Adapter: `src/infrastructure/llm/gemini_client.py`.
- Implementasyon: **resmi `google-genai` SDK'sı**.
- Model: `gemini-2.0-flash` default (env'de `gemini-2.5-flash` veya `pro`
  override edilebilir).
- API key Google AI Studio'dan alınır (ücretsiz).

### 3. Sağlayıcı seçimi

- `Settings` config'inde `llm_provider: Literal["minimax", "gemini"] = "minimax"`.
- Composition root (`src/presentation/main.py`) `LLM_PROVIDER` env değerine
  göre uygun adapter'ı `LLMClient` port'una bağlar.
- Runtime'da otomatik fallback yok; sağlayıcı seçimi statik, env-driven.
  Otomatik failover gerekirse **ayrı bir ADR** ile eklenir.

### 4. Port arayüzü (`application/ports/llm_client.py`)

Sağlayıcı-bağımsız dataclass'lar:

- `Message`: `role`, `content`, `tool_calls`, `tool_call_id`, `name`,
  `reasoning_details` (opsiyonel, MiniMax M2.7 reasoning chain için).
- `ToolDefinition`: `name`, `description`, `parameters_schema` (JSON Schema).
- `ToolCall`: `id`, `name`, `arguments` (dict).
- `LLMResponse`: `message` (assistant message), `tool_calls` (varsa),
  `finish_reason`, `raw_provider_payload` (opsiyonel, debug için).

Port metodları:

- `async chat(messages: list[Message], tools: list[ToolDefinition] | None = None,
  *, model: str | None = None) -> LLMResponse`

Sağlayıcıya özel parametreler (örn. Gemini'nin `safety_settings`, MiniMax'in
`temperature`) **adapter konfigürasyonunda** ya da kısıtlı bir `provider_options`
dict'inde taşınır; port arayüzü sağlayıcıya özel parametreyi ifşa etmez.

### 5. Reasoning state kuralı (M2.7 caveat'i)

Conversation state (`src/agent/conversation.py`) modelin yanıtını saklarken:

- **Tüm reasoning/thinking blokları korunur** (truncate yasak).
- **`tool_calls` listesi tam saklanır** (parçalı kaydetmek yasak).
- **`reasoning_details` alanı**, MiniMax adapter'ı tarafından doldurulduysa,
  sonraki çağrılarda **olduğu gibi geri gönderilir**.
- Gemini adapter'ı `reasoning_details` üretmez; bu durumda alan `None` kalır
  ve adapter onu görmezden gelir. Bu nedenle ortak port dataclass'ında alan
  opsiyoneldir.

Bu kural, adapter'ın kendi içinde değil **conversation state seviyesinde**
zorlanır; her iki sağlayıcı için aynı state davranışını garantiler.

### 6. Maliyet ve rate limit pratiği

- MiniMax: pay-as-you-go; hackathon ölçeğinde maliyet < $5 beklenir.
  `Settings`'te `minimax_api_key` zorunlu.
- Gemini: free tier (dakikada ~15 istek, günde ~1500 istek
  `gemini-2.0-flash` için tipik); demo + test için fazlasıyla yeterli.
  `Settings`'te `google_api_key` zorunlu.
- Adapter'lar rate limit hatası aldığında **exponential backoff** ile **en
  fazla 3 deneme** yapar; sonra `LLMRateLimitError` (port'ta tanımlı) fırlatır.
  Üst katmanlar bu hatayı kullanıcıya anlamlı bir mesajla aktarır.

## Alternatives considered

| Alternatif | Neden elendi? |
|------------|---------------|
| **Anthropic Claude (Haiku 4.5 / Sonnet 4.6) birincil** | Tool calling en güçlü olabilirdi ve mevcut ortamda `claude-api` skill desteği var; ancak ücretli (kişisel bütçe yok) ve Türkiye'den kredi kartı sürtünmesi raporlanıyor. |
| **OpenAI gpt-4o-mini birincil** | Tool calling standart, SDK olgun; ancak ücretli ve API key edinme süreci Türkiye için zaman zaman sorunlu. |
| **MiniMax M2.7 tek sağlayıcı (Gemini yok)** | Tek sağlayıcıya bağımlılık riski. Çoklu sağlayıcı port/adapter mimarisinin somut bir kanıtı olmakla beraber küçük ek maliyetle elde ediliyor; yarı yatırım. |
| **Gemini birincil, MiniMax fallback** | Gemini SDK olgunluğu ve free tier cömertliği avantaj; ancak mevcut MiniMax yatırımı + araştırmanın gösterdiği güçlü tool calling benchmark'ları MiniMax'i birincile çekti. Demo'da maliyeti olmayan iki sağlayıcıdan birincisi olmak fark yaratmıyor; sıralama mevcut kod yatırımına göre belirlendi. |
| **Eşit primary, runtime'da seçim** | Karmaşıklık ekler (her iki adapter test edilmeli, env değişkeni gizli sıçramaları doğurur). `LLM_PROVIDER` env ile statik seçim yeterli sade çözüm. |
| **MiniMax'i mevcut `httpx` ile koruyup OpenAI SDK'ya geçmemek** | Mevcut kod bütüncül değil; retry yok, streaming yok, tip güvenliği yok. OpenAI SDK base_url override ile **mevcut MiniMax adapter'ı yeniden yazılır**, hem resmi yol hem daha az kod. |
| **Otomatik failover (primary fail → fallback'e geç)** | Hata yönetimi karmaşıklığı, demo'da gizli sıçrama riski. Hackathon ölçeğinde gereksiz; statik env seçimi yeterli. İhtiyaç doğarsa ayrı ADR. |
| **MiniMax Anthropic uyumlu endpoint'i kullanmak** | Mümkün ama hibrit hissi var; OpenAI uyumlu endpoint daha düz, daha az şaşırtıcı. |
| **Türkçe için ön smoke test yapmak** | Mevcut sistem promptu zaten Türkçe çalışıyor; MiniMax çoklu dil desteği dökümante; smoke test hackathon zamanını yer, fayda marjinal. |
| **Open-source model (Llama, Qwen) yerel/Groq** | Yerel GPU yok; inference provider (Groq, Together) sıfır maliyetli olmayabilir. Türkçe + tool calling kombinasyonunda küçük open-source modellerde kalite belirsiz. |

## Consequences

### Olumlu

- **Sıfır/çok düşük maliyetle çalışır prototip** — hackathon bütçesi 0 olarak
  kalır.
- **Tool calling güçlü** — araştırma M2.7'nin Tier-1 sınıfında olduğunu
  gösterdi; agent katmanı sağlam çalışacak.
- **Çoklu sağlayıcı = mimari iddia** — sunumda "aynı agent, iki sağlayıcı, env
  değişkeniyle geçiş" hikâyesi port/adapter disiplinini somut gösteriyor.
- **OpenAI SDK + base_url** yolu, gelecekte OpenAI'a (veya başka uyumlu
  sağlayıcılara) geçişi bedavaya getirir — sadece `base_url` ve key değişir.
- **Reasoning state kuralı yazılı** → multi-turn tool calling'de sessiz hatalar
  önceden engellenir; M2.7'nin caveat'i kod tabanında dökümante.
- Mevcut MiniMax yatırımı boşa gitmedi; sadece adapter yeniden yazıldı.

### Olumsuz

- İki adapter yazmak ve her ikisini de test etmek, tek adapter'a kıyasla ek
  iş. Karşılığında: port mimarisi sağlamlığını doğrular, demo hikâyesi güçlenir.
- MiniMax'in reasoning_details kuralı **dikkat ister**; conversation state
  tasarımında ihlal kolay ve sonuçları sessiz. Test stratejisinde bunu
  spesifik test eden bir senaryo gerekiyor.
- Gemini SDK ile MiniMax/OpenAI SDK farklı async kalıpları kullanır; port
  arayüzü her ikisini de uyumlu örtmek zorunda. Adapter'larda bazı çevrim
  kodu zorunlu.
- MiniMax M2.7 görece yeni (2026-03); API değişiklik riski Anthropic/OpenAI'a
  kıyasla biraz daha yüksek. Karşılığında OpenAI uyumlu endpoint kullandığımız
  için kırılma sınırı dar.

## Open items

- [ ] `application/ports/llm_client.py` port arayüzünü ve dataclass'larını
      yaz (`Message`, `ToolDefinition`, `ToolCall`, `LLMResponse`,
      `LLMRateLimitError`).
- [ ] `infrastructure/llm/minimax_client.py` adapter'ı: `openai` SDK +
      `base_url="https://api.minimax.io/v1"`; mevcut `main.py`'daki
      MiniMax kodunu temizle.
- [ ] `infrastructure/llm/gemini_client.py` adapter'ı: `google-genai` SDK ile.
- [ ] `pyproject.toml` dependency güncellemeleri: `openai>=1.40,<2`,
      `google-genai` (resmi paket adı doğrulanacak).
- [ ] `Settings` (`pydantic-settings`) içine: `llm_provider`, `minimax_api_key`,
      `minimax_model`, `google_api_key`, `gemini_model`.
- [ ] `.env.example` güncellemesi: yeni env değişkenleri + açıklama yorumları.
- [ ] `conversation.py` reasoning_details / tool_calls / thinking bloklarını
      truncate etmeyen state davranışı; test edilebilir tasarım.
- [ ] Adapter testleri: `FakeOpenAIClient` + `FakeGoogleClient` ile birim
      test; en az 1 entegrasyon testi her sağlayıcı için (`--run-live`
      flag'iyle, CI'da default skip).
- [ ] Adapter'larda exponential backoff (en fazla 3 deneme) + rate limit
      hatası dönüştürme (port'taki `LLMRateLimitError`).
- [ ] Sunum/README'de "iki sağlayıcı, port/adapter ile geçiş" hikâyesini
      yazıya dök.

## Affected areas

- `src/infrastructure/llm/minimax_client.py` — yeni dosya, mevcut MiniMax
  kodunun temizlenmiş hali.
- `src/infrastructure/llm/gemini_client.py` — yeni dosya.
- `src/application/ports/llm_client.py` — port arayüzü ve ortak dataclass'lar.
- `src/agent/conversation.py` — reasoning/thinking/tool_calls state kuralı.
- `src/presentation/main.py` — composition root, `LLM_PROVIDER` env'e göre
  binding.
- `src/presentation/config/settings.py` — env-driven config.
- `pyproject.toml` — yeni bağımlılıklar (`openai`, `google-genai`); eski
  `httpx`-direkt-MiniMax kodu gerek bırakmıyor (httpx hâlâ kalır,
  notifier'lar için).
- `.env.example` — yeni env değişkenleri.
- [[0002-mimari-yaklasim-layered-agent]] — bu ADR oradaki agent katmanını
  somut sağlayıcılarla besler.
- [[0004-agent-cercevesi-langchain-langgraph-kullanilmamasi]] — bu ADR
  oradaki "sağlayıcı SDK yalnızca infrastructure/llm içinde" kuralının
  somut implementasyonu.
