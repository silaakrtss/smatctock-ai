# Chapter 13: Concurrency

> "Objects are abstractions of processing. Threads are abstractions of schedule." — James O. Coplien

## Özet

Eşzamanlılık programlamanın en zor konularından biridir. Temel mesaj: eşzamanlı kodu iş mantığından **tamamen ayır**, paylaşılan veriyi **minimumda tut**.

## Mitler vs Gerçekler

| Mit | Gerçek |
|-----|--------|
| "Her zaman performansı artırır" | Sadece bekleme-yoğun işlemlerde |
| "Tasarım değişmez" | Temelden farklı tasarım gerektirir |
| "Anlaması kolay" | En zor konulardan biri |

## Savunma Prensipleri

### 1. SRP: Eşzamanlılık kodunu iş mantığından ayır

```
// KÖTÜ: Karışık
public synchronized void processOrder(Order order) {
    validateOrder(order);    // Business logic
    saveToDatabase(order);   // I/O
}

// İYİ: Ayrılmış
public class OrderProcessor {
    public Order process(Order order) { validateOrder(order); return order; }
}
public class OrderConcurrencyManager {
    public CompletableFuture<Void> processAsync(Order order) { /* ... */ }
}
```

### 2. Paylaşılan Veri Kapsamını Sınırla

```
// KÖTÜ: Public mutable state
public int count = 0;

// İYİ: Thread-safe
private final AtomicInteger count = new AtomicInteger(0);
```

### 3. Verilerin Kopyalarını Kullan

```
// İYİ: Immutable kopya dön
public List<Flight> getFlights() {
    return List.copyOf(flights);
}
```

### 4. Thread'ler Birbirinden Bağımsız Olsun

## Thread-Safe Koleksiyonlar

| Geleneksel | Thread-Safe Alternatif |
|------------|----------------------|
| `HashMap` | `ConcurrentHashMap` |
| `ArrayList` | `CopyOnWriteArrayList` |
| `LinkedList` (kuyruk) | `LinkedBlockingQueue` |

## Execution Modelleri

- **Producer-Consumer:** Kuyruk ile veri akışı
- **Readers-Writers:** ReadWriteLock ile eşzamanlı okuma
- **Dining Philosophers:** Deadlock riski, kaynak sıralama

## Synchronized Bölümler Küçük Olsun

Sadece gereken yeri kilitle, tüm metodu değil.

## Graceful Shutdown Zordur

Erken düşün, erken kodla. Poison pill pattern kullan.

## Test Kuralı

> "Arada sırada olan hataları thread sorunu olarak ele al. Kozmik ışın diye geçiştirme."

## AI Agent İçin Kontrol Listesi

- [ ] Eşzamanlı kod, iş mantığından ayrılmış mı?
- [ ] Paylaşılan mutable state minimumda mı?
- [ ] Thread-safe collection'lar kullanılıyor mu?
- [ ] Synchronized bölümler mümkün olduğunca küçük mü?
- [ ] Immutable veri yapıları tercih edilmiş mi?
- [ ] Graceful shutdown düşünülmüş mü?
- [ ] Arada sırada oluşan test hataları ciddiye alınıyor mu?
