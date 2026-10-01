from flask import Response

from app import db, oauth
from app.models import Click, Link


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
        return link.id


def test_url_com_protocolo_invalido_retorna_400(client, user_teste):
    autenticar(client, user_teste)

    resposta = client.post(
        "/links",
        json={"original_url": "javascript:alert(1)"},
    )

    assert resposta.status_code == 400


def test_url_maior_que_limite_retorna_400(client, user_teste):
    autenticar(client, user_teste)
    url_longa = "https://example.com/" + "a" * 2000

    resposta = client.post(
        "/links",
        json={"original_url": url_longa},
    )

    assert resposta.status_code == 400


def test_requisicao_maior_que_limite_retorna_413(client, user_teste):
    autenticar(client, user_teste)

    resposta = client.post(
        "/links",
        data=b"x" * (7 * 1024 + 1),
        content_type="application/json",
    )

    assert resposta.status_code == 413


def test_decimo_primeiro_link_retorna_403(client, app, user_teste):
    autenticar(client, user_teste)

    for numero in range(10):
        criar_link(app, user_teste, f"link{numero}")

    resposta = client.post(
        "/links",
        json={"original_url": "https://example.com"},
    )

    assert resposta.status_code == 403


def test_link_inativo_retorna_404_sem_registrar_clique(client, app, user_teste):
    criar_link(app, user_teste, "inativo", ativo=False)

    resposta = client.get("/inativo")

    assert resposta.status_code == 404

    with app.app_context():
        assert db.session.query(Click).count() == 0


def test_logout_limpa_sessao(client, user_teste):
    autenticar(client, user_teste)

    resposta_logout = client.post("/logout")
    resposta_links = client.post(
        "/links",
        json={"original_url": "https://example.com"},
    )

    assert resposta_logout.status_code == 302
    assert resposta_links.status_code == 401


def test_login_retorna_429_apos_dez_tentativas(client, monkeypatch):
    monkeypatch.setattr(
        oauth.google,
        "authorize_redirect",
        lambda redirect_uri: Response(status=302),
    )

    for _ in range(10):
        resposta = client.get("/login")
        assert resposta.status_code == 302

    resposta = client.get("/login")

    assert resposta.status_code == 429
