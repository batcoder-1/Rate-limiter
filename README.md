# Rate Limiter

A Redis-backed, distributed rate limiter for Python implementing four classic algorithms. All rate-limiting logic runs inside **atomic Lua scripts** on the Redis server, making every check-and-update a single round-trip with no race conditions — even under high concurrency.

---

## Features

- **Four algorithms** — Token Bucket, Leaky Bucket, Sliding Window Log, Sliding Window Counter
- **Atomic operations** — each algorithm is a single Redis `EVAL` (Lua script), so concurrent requests never race
- **Per-user limiting** — keys are namespaced as `<namespace>:<user_id>`
- **Automatic key expiry** — TTLs are set so stale keys clean themselves up
- **Factory API** — one-line instantiation via a human-readable algorithm name

---

## Project Structure

```
Rate-Limiter/
├── base.py                          # Abstract base class (BaseClass)
├── factory.py                       # RateLimiter() factory function
├── token_bucket.py                  # Token Bucket implementation
├── leaky_bucket.py                  # Leaky Bucket implementation
├── sliding_window_log.py            # Sliding Window Log implementation
├── sliding_window_counter.py        # Sliding Window Counter implementation
├── scripts/
│   ├── token_bucket.lua             # Lua script – Token Bucket
│   ├── leaky_bucket.lua             # Lua script – Leaky Bucket
│   ├── sliding_window_log.lua       # Lua script – Sliding Window Log
│   └── sliding_window_counter.lua   # Lua script – Sliding Window Counter
└── test.py                          # Concurrent burst tests
```

---

## Prerequisites

- **Python 3.8+**
- **Redis server** running locally (default `localhost:6379`)
- **`redis-py`** — `pip install redis`

---

## Quick Start

```python
import redis
from factory import RateLimiter

r = redis.Redis(host="localhost", port=6379)

# Pick an algorithm by name
limiter = RateLimiter(
    "token bucket",
    redis_client=r,
    nameSpace="api",
    bucket_capacity=100,
    refill_rate=10,        # tokens per second
)

if limiter.isAllow("user_42"):
    print("Request allowed")
else:
    print("Rate limited")
```

---

## Algorithms

### 1. Token Bucket

Maintains a bucket of tokens that refills at a constant rate. Each request consumes one token; when the bucket is empty the request is denied. Allows short bursts up to `bucket_capacity`.

```python
limiter = RateLimiter(
    "token bucket",
    redis_client=r,
    nameSpace="my_api",
    bucket_capacity=50,    # max burst size
    refill_rate=5,         # tokens added per second
)
```

| Parameter | Description |
|---|---|
| `bucket_capacity` | Maximum number of tokens the bucket can hold |
| `refill_rate` | Tokens added per second |

### 2. Leaky Bucket

Models a bucket that leaks at a fixed rate. Incoming requests fill the bucket; if it overflows the request is rejected. Produces a smoothed, constant output rate.

```python
limiter = RateLimiter(
    "leaky bucket",
    redis_client=r,
    nameSpace="my_api",
    bucket_capacity=50,    # max queued requests
    leakage_rate=5,        # requests drained per second
)
```

| Parameter | Description |
|---|---|
| `bucket_capacity` | Maximum number of pending requests |
| `leakage_rate` | Requests drained per second |

### 3. Sliding Window Log

Keeps a sorted-set log of every request timestamp within the window. Before admitting a request, expired entries are pruned and the remaining count is compared to the limit. Most accurate, but uses more memory.

```python
limiter = RateLimiter(
    "sliding window log",
    redis_client=r,
    nameSpace="my_api",
    rate_limit=100,        # max requests per window
    window_size=60,        # window in seconds
)
```

| Parameter | Description |
|---|---|
| `rate_limit` | Maximum allowed requests in the window |
| `window_size` | Window duration in seconds |

### 4. Sliding Window Counter

Approximates a sliding window by weighting the previous window's count against the current one. Uses constant memory (a single hash per user) while still smoothing out boundary spikes.

```python
limiter = RateLimiter(
    "sliding window counter",
    redis_client=r,
    nameSpace="my_api",
    rate_limit=100,        # max requests per window
    window_size=60,        # window in seconds
)
```

| Parameter | Description |
|---|---|
| `rate_limit` | Maximum allowed requests in the window |
| `window_size` | Window duration in seconds |

---

## Algorithm Comparison

| | Token Bucket | Leaky Bucket | Sliding Window Log | Sliding Window Counter |
|---|---|---|---|---|
| **Burst tolerance** | ✅ Yes (up to capacity) | ❌ No (smoothed output) | ❌ No (hard cap) | ⚠️ Approximate |
| **Accuracy** | Exact | Exact | Exact | Approximate |
| **Memory per user** | O(1) — hash | O(1) — hash | O(n) — sorted set | O(1) — hash |
| **Redis data structure** | Hash | Hash | Sorted Set + Counter | Hash |
| **Best for** | APIs allowing bursts | Smoothing traffic | Strict per-window caps | High-throughput, low-memory |

---

## Running the Tests

The test file fires concurrent burst requests using `ThreadPoolExecutor` to verify that the Lua scripts are race-condition free:

```bash
# Make sure Redis is running, then:
python test.py
```

A passing run prints:

```
Total requests: 50
Allowed: 10
Denied: 40
Expected allowed: exactly 10
PASS: exactly rate_limit requests were allowed on a fresh window, no race condition.
```

---

## How It Works — Architecture

```
┌────────────┐         ┌─────────────────────┐         ┌────────────┐
│  Your App  │──call──▶│  Python Wrapper      │──EVAL──▶│   Redis    │
│            │         │  (token_bucket.py …) │         │  Lua Script│
│            │◀─bool───│                      │◀─0/1────│  (atomic)  │
└────────────┘         └─────────────────────┘         └────────────┘
```

1. The **Python class** loads the corresponding Lua script from `scripts/` and registers it with Redis via `register_script()`.
2. On every `isAllow(user_id)` call, the script is executed atomically on the Redis server — no multi-step transactions or locks needed.
3. The script returns `true` (allowed) or `false` (denied), which the Python side casts to a `bool`.

---

## License

This project is provided as-is for educational and practical use.
