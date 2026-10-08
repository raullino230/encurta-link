from app import db
from app.models import Link


def autenticar(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def criar_link(app, user_id, short_code, ativo=True):
    with app.app_context():
        link = Link(
            original_url="https://example.com",
            short_code=short_code,
            user_id=user_id,
            is_active=ativo,
        )
        db.session.add(link)
        db.session.commit()


def test_404_rota_inexistente_retorna_pagina_tematica(client):
    resposta = client.get("/rota-que-nao-existe")

    assert resposta.status_code == 404
    assert b"404" in resposta.data
    assert b"erro-container" in resposta.data


def test_404_link_inativo_retorna_pagina(client, app, user_teste):
    criar_link(app, user_teste, "inativo1", ativo=False)

    resposta = client.get("/inativo1")

    assert resposta.status_code == 404
    assert b"erro-container" in resposta.data


def test_erro_em_links_retorna_json(client):
    # Exige que o POST /links sem login use abort(401) no links.py
    resposta = client.post("/links", json={"original_url": "https://example.com"})

    assert resposta.status_code == 401
    assert "erro" in resposta.get_json()


def test_csrf_ausente_retorna_400_em_json(client, app, user_teste):
    app.config["WTF_CSRF_ENABLED"] = True
    autenticar(client, user_teste)

    resposta = client.post("/links", json={"original_url": "https://example.com"})

    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()


def test_429_retorna_pagina_de_rate_limit(client):
    ultima = None
    for _ in range(11):
        ultima = client.get("/login")

    assert ultima.status_code == 429
    assert b"muitas" in ultima.data.lower()