import redis
from fastapi import HTTPException

r = redis.Redis(host="localhost", port=6379, db=0)

def check_rate_limit(identifier: str)-> bool:
    key = f"rate_limit:{identifier}"
    request_count = r.incr(key)
    if request_count > 10:
        return False
    if request_count == 1: 
        r.expire(key, 60)
    return True
