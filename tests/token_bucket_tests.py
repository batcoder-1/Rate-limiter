from factory import RateLimiter
import redis
import time
r = redis.Redis(host="localhost", port=6379)
import pytest


def test_token_bucket_allows_up_to_capacity_and_refill():
    bucket_capacity = 10
    refill_rate = 1
    r.delete("token_bucket_test:user_1")

    limiter = RateLimiter(
        "token bucket",
        redis_client=r,
        nameSpace="token_bucket_test",
        bucket_capacity=bucket_capacity,
        refill_rate=refill_rate,
    )

    for request in range(1, 11):
        assert limiter.isAllow("user_1") == True, f"Request {request} should have been allowed"
    
    assert limiter.isAllow("user_1")==False,f"Request 11 should have been rejected "
    time.sleep(1)
    assert limiter.isAllow("user_1")==True,f"Request 12 should have been accepted "
    

def test_token_bucket_different_namspace_and_user():
    bucket_capacity=1
    refill_rate=1
    r.delete("login:user_1")
    r.delete("signup:user_1")
    limiter_login=RateLimiter(
        "token bucket",
        redis_client=r,
        nameSpace="login",
        bucket_capacity=bucket_capacity,
        refill_rate=refill_rate
    )
    limiter_signup=RateLimiter(
            "token bucket",
            redis_client=r,
            nameSpace="signup",
            bucket_capacity=bucket_capacity,
            refill_rate=refill_rate
        )
    assert limiter_login.isAllow("user_1") is True, f"Request one should be accepted"
    assert limiter_signup.isAllow("user_1") is True, f"Request two should be accepted"
    assert limiter_signup.isAllow("user_1") is False,f"Request three should be accepted"
    assert limiter_signup.isAllow("user_2") is True, f"Request four should be accepted"
    
def test_token_bucket_refill():
    bucket_capacity=3
    refill_rate=1
    r.delete("test_token_bucket:user_1")
    limiter=RateLimiter(
        "token bucket",
                redis_client=r,
                nameSpace="test_token_bucket",
                bucket_capacity=bucket_capacity,
                refill_rate=refill_rate
        )
    
    for request in range(1,4):
        assert limiter.isAllow("user_1") is True ,f"Request {request} should be accepted"
    
    assert limiter.isAllow("user_1") is False ,f"Request 4 should be rejected"
    time.sleep(3)
    for request in range(5,8):
            assert limiter.isAllow("user_1") is True ,f"Request {request} should be accepted"
        
    assert limiter.isAllow("user_1") is False ,f"Request 8 should be rejected"
    
def test_token_bucket_invalid_bucket_capacity():
    r.delete("test_token_bucket:user_1")
    with pytest.raises(ValueError):
        limiter=RateLimiter(
            "token bucket",
                    redis_client=r,
                    nameSpace="test_token_bucket",
                    bucket_capacity=-1,
                    refill_rate=1
            )
def test_token_bucket_invalid_refill_rate():
    with pytest.raises(ValueError):
            limiter=RateLimiter(
                "token bucket",
                        redis_client=r,
                        nameSpace="test_token_bucket",
                        bucket_capacity=1,
                        refill_rate=0
                )