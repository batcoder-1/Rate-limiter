# redis-ratekit

[![PyPI version](https://img.shields.io/pypi/v/redis-ratekit.svg)](https://pypi.org/project/redis-ratekit/)
[![Python](https://img.shields.io/pypi/pyversions/redis-ratekit.svg)](https://pypi.org/project/redis-ratekit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/batcoder-1/Rate-limiter/blob/main/LICENSE)

Atomic, Redis-backed rate limiting for Python.

Each algorithm runs as a single atomic Lua script on the Redis server. Tested with: single Redis server, Redis 8.1.0, Python 3.14.

---

## ✨ Highlights

- **Four algorithms** in one package — pick the right trade-off for your use case
- **Single atomic Lua scripts** — each algorithm runs as one Redis script per check
- **Per-user / per-resource keys** — namespaced as `<namespace>:<user_id>`
- **Automatic key expiry** — stale keys clean themselves up via TTL
- **Factory API** — one-liner instantiation by algorithm name
- **Input validation** — bad parameters raise `ValueError` immediately

---

## Installation

```bash
pip install redis-ratekit
```

> **Requires** Python ≥ 3.14 and a running Redis server.

---

## Quick Start

```python
import redis
from ratekit import RateLimiter

r = redis.Redis(host="localhost", port=6379)

# Create a limiter — just pass the algorithm name
limiter = RateLimiter(
    "token bucket",
    redis_client=r,
    nameSpace="api",
    bucket_capacity=100,
    refill_rate=10,        # tokens per second
)

if limiter.isAllow("user_42"):
    print("✅ Request allowed")
else:
    print("🚫 Rate limited")
```

Note: `nameSpace` and `isAllow` are camelCase by design.

---

## Algorithms

### Token Bucket

Maintains a bucket of tokens that refills at a constant rate. Each request consumes one token; when the bucket is empty the request is denied. **Allows short bursts** up to `bucket_capacity`.

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

### Leaky Bucket

Models a bucket that leaks at a fixed rate. Incoming requests fill the bucket; if it overflows the request is rejected. Produces a **smoothed, constant output rate**.

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

### Sliding Window Log

Keeps a sorted-set log of every request timestamp within the window. Before admitting a request, expired entries are pruned and the remaining count is compared to the limit. **Most accurate**, but uses more memory.

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

### Sliding Window Counter

Approximates a sliding window by weighting the previous window's count against the current one. Uses **constant memory** (a single hash per user) while still smoothing out boundary spikes.

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
| **Redis data type** | Hash | Hash | Sorted Set + seq counter | Hash |
| **Best for** | APIs allowing bursts | Smoothing traffic | Strict per-window caps | High-throughput, low-memory |

---

## How It Works

```
┌────────────┐         ┌──────────────────────┐         ┌────────────┐
│  Your App  │──call──▶│  Python wrapper       │──EVAL──▶│   Redis    │
│            │         │  (Token_Bucket, …)    │         │  Lua script│
│            │◀─bool───│                       │◀─0/1────│  (atomic)  │
└────────────┘         └──────────────────────┘         └────────────┘
```

1. The Python class loads a Lua script from the bundled `scripts/` directory and registers it with Redis via `register_script()`.
2. The current timestamp is generated inside each Lua script with `redis.call("TIME")` on the Redis server, so the decision is based on the Redis clock rather than a Python-side timestamp.
3. On every `isAllow(user_id)` call the script executes atomically on the Redis server.
4. The script returns `1` (allowed) or `0` (denied), cast to a Python `bool`.

Redis connection errors propagate from `redis-py` (for example, `redis.exceptions.ConnectionError`). This library does not catch or swallow them; the calling application decides whether to fail open or closed.

---

## Development

Contributors can set up a local checkout like this:

```bash
git clone https://github.com/batcoder-1/Rate-limiter.git
cd Rate-limiter
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest
pytest tests/ -v
```

Tests require a Redis server running on `localhost:6379`.

Tests cover:

- ✅ Basic allow / deny behaviour
- ✅ Refill / leakage after a sleep
- ✅ Per-namespace and per-user isolation
- ✅ Input validation (`ValueError` on bad parameters)
- ✅ Concurrent burst requests via `ThreadPoolExecutor` + `Barrier`
- ✅ Sliding window counter weighting logic

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/batcoder-1/Rate-limiter).

---

## License

Distributed under the **MIT License**. See [`LICENSE`](https://github.com/batcoder-1/Rate-limiter/blob/main/LICENSE) for details.
