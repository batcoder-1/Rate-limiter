from factory import RateLimiter
import pytest
import redis
import time
r=redis.Redis(host="localhost",port=6379)

def test_leaky_bucket_invalid_bucket_capacity():
    with pytest.raises(ValueError):
        r.delete("test_leaky_bucket:user_1")
        limiter=RateLimiter(
            "leaky bucket",
            redis_client=r,
            nameSpace="test_leaky_bucket",
            bucket_capacity=-1,
            leakage_rate=1,
        )
def test_leaky_bucket_invalid_refill_rate():
    with pytest.raises(ValueError):
        r.delete("test_leaky_bucket:user_1")
        limiter=RateLimiter(
            "leaky bucket",
            redis_client=r,
            nameSpace="test_leaky_bucket",
            bucket_capacity=1,
            leakage_rate=-1,
        )
        
def test_leaky_bucket_different_namespace_and_user():
    r.delete(
    "test_leaky_bucket1:user_1",
    "test_leaky_bucket2:user_1",
    "test_leaky_bucket2:user_2",
    )
    limiter1=RateLimiter(
           "leaky bucket",
            redis_client=r,
            nameSpace="test_leaky_bucket1",
            bucket_capacity=1,
            leakage_rate=1,        
    )
    limiter2=RateLimiter(
               "leaky bucket",
                redis_client=r,
                nameSpace="test_leaky_bucket2",
                bucket_capacity=1,
                leakage_rate=1,        
        )
    assert limiter1.isAllow("user_1") is True , "Request 1 should be accepted"
    assert limiter2.isAllow("user_1") is True , "Request 2 should be accepted"
    assert limiter2.isAllow("user_1") is False , "Request 3 should be rejected"
    assert limiter2.isAllow("user_2") is True , "Request 4 should be accepted"
    
    
def test_leaky_bucket_allow_upto_capacity():
    r.delete("test_leaky_bucket:user_1")
    limiter=RateLimiter(
         "leaky bucket",
                redis_client=r,
                nameSpace="test_leaky_bucket",
                bucket_capacity=10,
                leakage_rate=1,
    )
    for request in range(1,11):
        assert limiter.isAllow("user_1") is True,f"Request {request} should be allowed"
    
    assert limiter.isAllow("user_1") is False ,"Request 11 should be rejected"
    time.sleep(1)
    assert limiter.isAllow("user_1") is True, "Request 12 should be allowed"
    
def test_leaky_bucket_leakage():
    r.delete("test_leaky_bucket:user_1")

    limiter = RateLimiter(
            "leaky bucket",
            redis_client=r,
            nameSpace="test_leaky_bucket",
            bucket_capacity=1,
            leakage_rate=1,
        )

    assert limiter.isAllow("user_1") is True
    assert limiter.isAllow("user_1") is False
    time.sleep(1.2)
    assert limiter.isAllow("user_1") is True
        
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
def test_leaky_bucket_concurrent_requests():
    r.delete("test_leaky_bucket:user_1")
    limiter=RateLimiter(
        "leaky bucket",
        redis_client=r,
        nameSpace="test_leaky_bucket",
        bucket_capacity=1,
        leakage_rate=1,
    )
    barrier=Barrier(2)
    
    def make_request():
        barrier.wait()
        return limiter.isAllow("user_1")
    
    with ThreadPoolExecutor(max_workers=2) as work:
        futures=[
            work.submit(
                make_request
            )
            for _ in range(1,3)
        ]
    responses = [future.result() for future in futures]
    
    allowed = sum(responses)
    rejected = len(responses) - allowed
    
    assert allowed == 1, f"Expected 1 allowed, got {allowed}"
    assert rejected == 1, f"Expected 1 rejected, got {rejected}"