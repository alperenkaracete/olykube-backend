import pytest

USER = {"email": "user@olykube.dev", "password": "s3cret"}

PROTECTED_ENDPOINTS = [
    ("get", "/protected", None),
    ("get", "/agents/", None),
    ("post", "/agents/", {"name": "a", "system_prompt": "p"}),
    ("get", "/agents/1", None),
    ("get", "/agents/name/a", None),
    ("delete", "/agents/?agent_name=a", None),
    ("post", "/agents/1/chat", {"message": "merhaba"}),
    ("get", "/agents/1/history/t1", None),
    ("post", "/ingest", {"text": "metin", "doc_id": "d1"}),
]


def test_register_and_login_with_json(client):
    assert client.post("/register", json=USER).status_code == 200

    response = client.post("/login", json=USER)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_form_like_swagger_authorize(client):
    client.post("/register", json=USER)

    response = client.post(
        "/login", data={"username": USER["email"], "password": USER["password"]}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]
    me = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert me.json() == {"email": USER["email"]}


def test_login_rejects_wrong_password_and_unknown_email(client):
    client.post("/register", json=USER)

    assert client.post("/login", json={**USER, "password": "yanlis"}).status_code == 401
    assert client.post("/login", json={**USER, "email": "yok@olykube.dev"}).status_code == 404


def test_register_rejects_duplicate_email(client):
    client.post("/register", json=USER)

    assert client.post("/register", json=USER).status_code == 400


@pytest.mark.parametrize("method,path,body", PROTECTED_ENDPOINTS)
def test_protected_endpoints_require_valid_token(client, method, path, body):
    kwargs = {"json": body} if body else {}

    no_token = getattr(client, method)(path, **kwargs)
    bad_token = getattr(client, method)(
        path, headers={"Authorization": "Bearer gecersiz"}, **kwargs
    )

    assert no_token.status_code == 401
    assert bad_token.status_code == 401


def test_agent_crud_with_token(client, auth_headers):
    agent = {"name": "devops", "system_prompt": "Kıdemli DevOps ajanısın."}

    assert client.post("/agents/", json=agent, headers=auth_headers).status_code == 200
    assert client.post("/agents/", json=agent, headers=auth_headers).status_code == 400

    listed = client.get("/agents/", headers=auth_headers).json()
    assert [a["name"] for a in listed] == ["devops"]
    assert listed[0]["model_name"] == "llama3"

    deleted = client.delete("/agents/?agent_name=devops", headers=auth_headers)
    assert deleted.status_code == 200
    assert client.get("/agents/", headers=auth_headers).json() == []
