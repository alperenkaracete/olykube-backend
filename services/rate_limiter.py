import time
import redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from core.config import REDIS_HOST, REDIS_PORT
from core.logger import logger

# Kısa timeout ve yeniden deneme yok: Redis erişilemezse istek askıda kalmasın
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    socket_connect_timeout=1,
    socket_timeout=1,
    retry=Retry(NoBackoff(), 0),
)

# Devre kesici: Redis hata verince bu süre boyunca hiç denenmez.
# (DNS çözümlemesi socket timeout'una dahil değil; her istekte tekrar denemek saniyeler sürer.)
REDIS_COOLDOWN_SECONDS = 30
_redis_down_until = 0.0

def check_rate_limit(identifier: str)-> bool:
    global _redis_down_until
    if time.monotonic() < _redis_down_until:
        return True

    key = f"rate_limit:{identifier}"
    try:
        request_count = r.incr(key)
        if request_count == 1:
            r.expire(key, 60)
    except redis.exceptions.RedisError as e:
        # Fail-open: Redis kapalıyken API'yi kilitlemek yerine isteği geçir
        _redis_down_until = time.monotonic() + REDIS_COOLDOWN_SECONDS
        logger.error(
            f"Rate limiter {REDIS_COOLDOWN_SECONDS} sn devre dışı, "
            f"Redis'e ulaşılamıyor ({REDIS_HOST}:{REDIS_PORT}): {e}"
        )
        return True
    return request_count <= 10
