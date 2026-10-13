from factory import RateLimiter
import pytest
import time
import redis

r=redis.Redis(host="localhost",port=6379)

def test_sliding_window_log_invalid_rate_limit():
    with pytest.raises(ValueError):
        limiter=RateLimiter(
            "sliding window log",
            redis_client=r,
            nameSpace="test_slwl",
            rate_limit=-1,
            window_size=1
        )
    
def test_sliding_window_log_invalid_window_size():
    with pytest.raises(ValueError):
        limiter=RateLimiter(
            "sliding window log",
            redis_client=r,
            nameSpace="test_slwl",
            rate_limit=1,
            window_size=-1
        )

def test_sliding_window_log_different_namespace_and_user():
    r.delete("test_slwl1:user_1"
             ,"test_slwl1:user_2"
             ,"test_slwl2:user_1"
             ,"test_slwl2:user_2"
             )
    limiter1=RateLimiter(
                "sliding window log",
                redis_client=r,
                nameSpace="test_slwl1",
                rate_limit=1,
                window_size=1
            )
    limiter2=RateLimiter(
                "sliding window log",
                redis_client=r,
                nameSpace="test_slwl2",
                rate_limit=1,
                window_size=1
            )
    
    assert limiter1.isAllow("user_1") is True , "Request 1 should be accepted"
    assert limiter2.isAllow("user_1") is True , "Request 2 should be accepted"
    assert limiter2.isAllow("user_1") is False, "Request 3 should be rejected"
    assert limiter2.isAllow("user_2") is True , "Request 4 should be accepted"
    
def test_sliding_window_log_window_size_and_rate_limit():
    r.delete("test_slwl:user_1")
    limiter=RateLimiter(
                "sliding window log",
                redis_client=r,
                nameSpace="test_slwl",
                rate_limit=10,
                window_size=1
            )
    for request in range(1,11):
        assert limiter.isAllow("user_1") is True , f"Request {request} should be accepted"
    
    assert limiter.isAllow("user_1") is False , "Request 11 should be rejected"
    time.sleep(1.2)
    assert limiter.isAllow("user_1") is True , "Request 12 should be accepted"
    
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

def test_sliding_window_log_concurrent_request():
    r.delete("test_slwl:user_1")
    limiter=RateLimiter(
                "sliding window log",
                redis_client=r,
                nameSpace="test_slwl",
                rate_limit=10,
                window_size=1
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
    