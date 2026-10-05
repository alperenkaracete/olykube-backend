def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_is_exempt_from_rate_limit(client, fake_redis):
    # K8s probe'ları sınırsız çağırabilmeli
    for _ in range(20):
        assert client.get("/health").status_code == 200

    assert fake_redis.store == {}
