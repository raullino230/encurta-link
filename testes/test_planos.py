from datetime import timedelta

from app import db
from app.models import Link, User, utcnow
from app.planos import PLANOS, obter_plano, limite_links


def autenticar(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def criar_link(app, user_id, short_code):
    with app.app_context():
        link = Link(
            original_url="https://example.com",
            short_code=short_code,
            user_id=user_id,
            is_active=True,
        )
        db.session.add(link)
        db.session.commit()


def criar_varios_links(app, user_id, quantidade):
    for numero in range(quantidade):
        criar_link(app, user_id, f"plano{numero}")


def definir_plano(app, user_id, plano, data_renovacao=None):
    with app.app_context():
        user = db.session.get(User, user_id)
        user.plano = plano
        user.data_renovacao = data_renovacao
        db.session.commit()


# ---------- is_pro e obter_plano ----------

def test_usuario_novo_e_gratuito(app, user_teste):
    with app.app_context():
        user = db.session.get(User, user_teste)

        assert user.plano == "gratuito"
        assert user.is_pro is False
        assert obter_plano(user) == "gratuito"


def test_pro_com_renovacao_futura_e_pro(app, user_teste):
    definir_plano(app, user_teste, "pro", utcnow() + timedelta(days=30))

    with app.app_context():
        user = db.session.get(User, user_teste)

        assert user.is_pro is True
        assert obter_plano(user) == "pro"


def test_pro_vencido_volta_a_gratuito(app, user_teste):
    definir_plano(app, user_teste, "pro", utcnow() - timedelta(days=1))

    with app.app_context():
        user = db.session.get(User, user_teste)

        assert user.plano == "pro"  # a coluna continua "pro" no banco
        assert user.is_pro is False
        assert obter_plano(user) == "gratuito"


def test_pro_sem_data_nao_e_pro(app, user_teste):
    definir_plano(app, user_teste, "pro", None)

    with app.app_context():
        user = db.session.get(User, user_teste)

        assert user.is_pro is False


def test_gratuito_com_data_futura_nao_e_pro(app, user_teste):
    definir_plano(app, user_teste, "gratuito", utcnow() + timedelta(days=30))

    with app.app_context():
        user = db.session.get(User, user_teste)

        assert user.is_pro is False


# ---------- limite de links por plano ----------

def test_limite_de_links_gratuito(client, app, user_teste):
    autenticar(client, user_teste)
    limite = PLANOS["gratuito"]["limite_links"]
    criar_varios_links(app, user_teste, limite)

    resposta = client.post("/links", json={"original_url": "https://example.com"})

    assert resposta.status_code == 403


def test_pro_passa_do_limite_do_gratuito(client, app, user_teste):
    definir_plano(app, user_teste, "pro", utcnow() + timedelta(days=30))
    autenticar(client, user_teste)
    criar_varios_links(app, user_teste, PLANOS["gratuito"]["limite_links"])

    resposta = client.post("/links", json={"original_url": "https://example.com"})

    assert resposta.status_code == 200
    assert "short_url" in resposta.get_json()


def test_limite_links_acompanha_o_plano(app, user_teste):
    with app.app_context():
        user = db.session.get(User, user_teste)
        assert limite_links(user) == PLANOS["gratuito"]["limite_links"]

    definir_plano(app, user_teste, "pro", utcnow() + timedelta(days=30))

    with app.app_context():
        user = db.session.get(User, user_teste)
        assert limite_links(user) == PLANOS["pro"]["limite_links"]


# ---------- página de configurações ----------

def test_configuracoes_gratuito_mostra_plano_limite_e_upgrade(client, user_teste):
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/configuracoes")
    limite = PLANOS["gratuito"]["limite_links"]

    assert b"Plano Gratuito" in resposta.data
    assert f"de {limite} links usados".encode() in resposta.data
    assert b"Fazer upgrade" in resposta.data


def test_configuracoes_pro_mostra_plano_e_esconde_upgrade(client, app, user_teste):
    definir_plano(app, user_teste, "pro", utcnow() + timedelta(days=30))
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/configuracoes")
    limite = PLANOS["pro"]["limite_links"]

    assert b"Plano Pro" in resposta.data
    assert f"de {limite} links usados".encode() in resposta.data
    assert b"Fazer upgrade" not in resposta.data


# ---------- comando flask definir-plano ----------

def test_comando_definir_plano_pro_e_volta_para_gratuito(app, user_teste):
    runner = app.test_cli_runner()

    resultado = runner.invoke(args=["definir-plano", "teste@example.com", "pro", "10"])
    assert resultado.exit_code == 0

    with app.app_context():
        user = db.session.get(User, user_teste)
        assert user.is_pro is True

    resultado = runner.invoke(args=["definir-plano", "teste@example.com", "gratuito"])
    assert resultado.exit_code == 0

    with app.app_context():
        user = db.session.get(User, user_teste)
        assert user.is_pro is False
        assert user.data_renovacao is None


def test_comando_definir_plano_usuario_inexistente_falha(app):
    runner = app.test_cli_runner()

    resultado = runner.invoke(args=["definir-plano", "ninguem@example.com", "pro"])

    assert resultado.exit_code != 0