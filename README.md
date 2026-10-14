# redis-ratekit

[![PyPI version](https://img.shields.io/pypi/v/redis-ratekit.svg)](https://pypi.org/project/redis-ratekit/)
[![Python](https://img.shields.io/pypi/pyversions/redis-ratekit.svg)](https://pypi.org/project/redis-ratekit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/batcoder-1/Redis-Ratekit/blob/main/LICENSE)

Atomic, Redis-backed rate limiting for Python.

Each algorithm runs as a single atomic Lua script on the Redis server. Tested with: single Redis server, Redis 8.1.0, Python 3.14.

---

## ✨ Highlights

- **Four algorithms** in one package — pick the right trade-off for your use case
- **Single atomic Lua scripts** — each algorithm runs as one Redis script per check, so concurrent requests cannot race
- **Per-user / per-resource keys** — namespaced as `<namespace>:<user_id>`
- **Automatic key expiry** — stale keys clean themselves up via TTL
- **Factory API** — one-liner instantiation by algorithm name
- **Input validation** — zero or negative parameters raise `ValueError` immediately

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

Every numeric parameter must be greater than 0. A zero or negative value raises `ValueError` when the limiter is created.

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
| `bucket_capacity` | Maximum number of tokens the bucket can hold (must be > 0) |
| `refill_rate` | Tokens added per second (must be > 0) |

### Leaky Bucket

Requests fill a bucket that drains at a fixed rate. A request is admitted if it fits without overflowing the bucket, and nothing is queued or delayed. Like a token bucket, it allows a burst up to `bucket_capacity` from idle, then admits at most `leakage_rate` requests per second on average. It tracks used capacity where a token bucket tracks remaining tokens.

```python
limiter = RateLimiter(
    "leaky bucket",
    redis_client=r,
    nameSpace="my_api",
    bucket_capacity=50,    # bucket size
    leakage_rate=5,        # drained per second
)
```

| Parameter | Description |
|---|---|
| `bucket_capacity` | How much the bucket holds before a request is rejected (must be > 0) |
| `leakage_rate` | Amount drained per second (must be > 0) |

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
| `rate_limit` | Maximum allowed requests in the window (must be > 0) |
| `window_size` | Window duration in seconds (must be > 0) |

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
| `rate_limit` | Maximum allowed requests in the window (must be > 0) |
| `window_size` | Window duration in seconds (must be > 0) |

---

## Algorithm Comparison

| | Token Bucket | Leaky Bucket | Sliding Window Log | Sliding Window Counter |
|---|---|---|---|---|
| **Limit shape** | Capacity + refill rate | Capacity + drain rate | N requests per rolling window | ≈ N requests per rolling window |
| **Accuracy** | Exact | Exact | Exact | Approximate |
| **Memory per key** | O(1) — hash | O(1) — hash | O(n) — sorted set | O(1) — hash |
| **Redis data type** | Hash | Hash | Sorted Set + seq counter | Hash |
| **Best for** | APIs that allow short bursts, then a steady rate | Same shape as a token bucket, modeled as capacity used | Strict, exact per-window caps | High-throughput, low-memory limiting |

Fixed-window counters are intentionally not included: a client can send a full quota at the end of one window and another full quota at the start of the next, doubling the intended rate at the boundary.

---

## How It Works

```
┌────────────┐         ┌──────────────────────┐         ┌────────────┐
│  Your App  │──call──▶│  Python wrapper       │──EVAL──▶│   Redis    │
│            │         │  (Token_Bucket, …)    │         │  Lua script│
│            │◀─bool───│                       │◀─1/nil──│  (atomic)  │
└────────────┘         └──────────────────────┘         └────────────┘
```

1. The Python class loads a Lua script from the bundled `scripts/` directory and registers it with Redis via `register_script()`.
2. The current timestamp is generated inside each Lua script with `redis.call("TIME")` on the Redis server, so the decision is based on the Redis clock rather than a Python-side timestamp.
3. On every `isAllow(user_id)` call the script executes atomically on the Redis server.
4. The script returns `1` (allowed) or nil (denied), cast to a Python `bool`.

Keys are `<namespace>:<key>`; the sliding window log also writes `<namespace>:<key>-seq`. Every write refreshes the key's TTL, which each algorithm derives internally from its own parameters, so there is nothing to configure.

Redis connection errors propagate from `redis-py` (for example, `redis.exceptions.ConnectionError`). This library does not catch or swallow them; the calling application decides whether to fail open or closed.

---

## Limitations

- **Limiting is per key.** It bounds each caller, not total server load. For an aggregate cap, run a second limiter with a fixed key (for example `"global"`) and check both.
- **Sliding window counter is an estimate.** It assumes requests in the previous window were evenly spread.
- **Sliding window log memory grows with traffic**, since it stores one entry per admitted request in the window.
- **Redis Cluster is untested.** The sliding window log uses two keys per caller that may land in different slots.

---

## Development

Contributors can set up a local checkout like this:

```bash
git clone https://github.com/batcoder-1/Redis-Ratekit.git
cd Redis-Ratekit
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest
pytest tests/ -v
```

Tests require a Redis server running on `localhost:6379`.

Tests cover:

- ✅ Basic allow / deny behaviour
- ✅ Refill / leakage after a sleep
- ✅ Per-namespace and per-user isolation
- ✅ Input validation (`ValueError` on zero or negative parameters)
- ✅ Concurrent burst requests via `ThreadPoolExecutor` + `Barrier`
- ✅ Sliding window counter weighting logic

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/batcoder-1/Redis-Ratekit).

---

## License

Distributed under the **MIT License**. See [`LICENSE`](https://github.com/batcoder-1/Redis-Ratekit/blob/main/LICENSE) for details.