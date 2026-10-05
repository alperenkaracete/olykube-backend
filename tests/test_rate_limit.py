from services import rate_limiter


def test_blocks_after_ten_requests_per_ip(client):
    statuses = [client.post("/register", json={}).status_code for _ in range(12)]

    # İlk 10 istek uygulamaya ulaşır (gövde boş olduğu için 422), sonrası 429
    assert statuses[:10] == [422] * 10
    assert statuses[10:] == [429, 429]


def test_limit_is_per_ip(fake_redis):
    for _ in range(10):
        assert rate_limiter.check_rate_limit("10.0.0.1")

    assert not rate_limiter.check_rate_limit("10.0.0.1")
    assert rate_limiter.check_rate_limit("10.0.0.2")


def test_redis_down_fails_open_without_500(client, down_redis):
    statuses = [client.get("/health").status_code for _ in range(3)]
    statuses += [client.post("/register", json={}).status_code for _ in range(12)]

    # Redis kapalıyken hiçbir istek 500 veya 429 almaz
    assert 500 not in statuses
    assert 429 not in statuses


def test_redis_down_is_not_retried_during_cooldown(down_redis):
    for _ in range(5):
        assert rate_limiter.check_rate_limit("10.0.0.1")

    # İlk hatadan sonra devre kesici açılır; Redis tekrar denenmez
    assert down_redis.calls == 1
