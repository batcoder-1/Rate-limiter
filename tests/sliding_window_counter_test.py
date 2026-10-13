from factory import RateLimiter
import pytest
import time
import redis

r=redis.Redis(host="localhost",port=6379)

def test_sliding_window_counter_invalid_rate_limit():
    with pytest.raises(ValueError):
        limiter=RateLimiter(
            "sliding window counter",
            redis_client=r,
            nameSpace="test_slwc",
            rate_limit=-1,
            window_size=1
        )
    
def test_sliding_window_counter_invalid_window_size():
    with pytest.raises(ValueError):
        limiter=RateLimiter(
            "sliding window counter",
            redis_client=r,
            nameSpace="test_slwc",
            rate_limit=1,
            window_size=-1
        )

def test_sliding_window_counter_different_namespace_and_user():
    r.delete("test_slwc1:user_1"
             ,"test_slwc1:user_2"
             ,"test_slwc2:user_1"
             ,"test_slwc2:user_2"
             )
    limiter1=RateLimiter(
                "sliding window counter",
                redis_client=r,
                nameSpace="test_slwc1",
                rate_limit=1,
                window_size=60
            )
    limiter2=RateLimiter(
                "sliding window counter",
                redis_client=r,
                nameSpace="test_slwc2",
                rate_limit=1,
                window_size=60
            )
    
    assert limiter1.isAllow("user_1") is True , "Request 1 should be accepted"
    assert limiter2.isAllow("user_1") is True , "Request 2 should be accepted"
    assert limiter2.isAllow("user_1") is False, "Request 3 should be rejected"
    assert limiter2.isAllow("user_2") is True , "Request 4 should be accepted"
    
def test_sliding_window_counter_window_size_and_rate_limit():
    r.delete("test_slwc:user_1")
    limiter=RateLimiter(
                "sliding window counter",
                redis_client=r,
                nameSpace="test_slwc",
                rate_limit=10,
                window_size=5
            )
    for request in range(1,11):
        assert limiter.isAllow("user_1") is True , f"Request {request} should be accepted"
    
    assert limiter.isAllow("user_1") is False , "Request 11 should be rejected"
    time.sleep(5.2)
    assert limiter.isAllow("user_1") is True , "Request 12 should be accepted"
    
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

def test_sliding_window_counter_concurrent_request():
    r.delete("test_slwc:user_1")
    limiter=RateLimiter(
                "sliding window counter",
                redis_client=r,
                nameSpace="test_slwc",
                rate_limit=10,
                window_size=60
            )
    barrier=Barrier(15)
    
    def make_request():
        barrier.wait()
        return limiter.isAllow("user_1")
    
    with ThreadPoolExecutor(max_workers=15) as work:
        futures=[
            work.submit(make_request)
            for _ in range(1,16)
        ]
    responses=[future.result() for future in futures]
    
    allowed=sum(responses)
    rejected=len(responses)-allowed
    
    assert allowed == 10, f"Expected 10 allowed, got {allowed}"
    assert rejected == 5, f"Expected 5 rejected, got {rejected}"
    
def test_sliding_window_counter_weighting():
    def wait_for_window_phase(window_size, target=0.75):
        while True:
            seconds, microseconds = r.time()
            timestamp = seconds + microseconds / 1_000_000

            window_id = int(timestamp // window_size)
            elapsed_fraction = (
                timestamp - window_id * window_size
            ) / window_size

            if abs(elapsed_fraction - target) < 0.01:
                return window_id

            time.sleep(0.01)
    window_size=10
    window_id=wait_for_window_phase(window_size)
    r.delete("test_slwc:user_1")

    limiter=RateLimiter(
        "sliding window counter",
        redis_client=r,
        nameSpace="test_slwc",
        rate_limit=10,
        window_size=window_size
    )
    r.hset(
            "test_slwc:user_1",
            mapping={
                "previous_window_id": window_id,
                "prev_count": 8,
                "current_count": 7,
            }
        )
    assert limiter.isAllow("user_1") is True , "Request 8 should be allowed"
    r.delete("test_slwc:user_1")
    window_id=wait_for_window_phase(window_size)
    r.hset(
            "test_slwc:user_1",
            mapping={
                "previous_window_id": window_id,
                "prev_count": 8,
                "current_count": 9,
            }
        )
    assert limiter.isAllow("user_1") is False , "Request 9 should be rejected"
    
    