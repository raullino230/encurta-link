from app import db, oauth
from app.models import Link, User




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

# ---------- /dashboard (Meus Links) ----------

def test_dashboard_sem_login_redirecionar_para_login(client):
    entrar_em_dashboard_sem_autenticar = client.get("/dashboard")

    assert entrar_em_dashboard_sem_autenticar.status_code == 302
    assert entrar_em_dashboard_sem_autenticar.headers["Location"].endswith("/login")


def test_dashboard_com_login_retorna_200(client, user_teste):
    autenticar(client, user_teste)

    entrar_dashboard_com_login = client.get("/dashboard")

    assert entrar_dashboard_com_login.status_code == 200


def test_dashboard_mostra_links_do_usuario(client, app, user_teste):
   
    criar_link(app, user_teste, "test123")
    criar_link(app, user_teste, "teste_234")

    autenticar(client, user_teste)

    entrar_dashboard = client.get("/dashboard")

    assert b"test123" in entrar_dashboard.data
    assert b"teste_234" in entrar_dashboard.data


# ---------- /dashboard/analytics ----------

def test_analytics_sem_login_redireciona_para_login(client):
    entrar_em_analytics_sem_autenticar = client.get("/dashboard/analytics")

    assert entrar_em_analytics_sem_autenticar.status_code == 302
    assert entrar_em_analytics_sem_autenticar.headers["Location"].endswith("/login")

def test_analytics_com_login_retorna_200(client, user_teste):
    autenticar(client, user_teste)

    entrar_analytics_com_login = client.get("/dashboard/analytics")

    assert entrar_analytics_com_login.status_code == 200

# ---------- /dashboard/configuracoes ----------

def test_configuracoes_sem_login_redireciona_para_login(client):
    entrar_em_configuracoes_sem_autenticar = client.get("/dashboard/configuracoes")

    assert entrar_em_configuracoes_sem_autenticar.status_code == 302
    assert entrar_em_configuracoes_sem_autenticar.headers["Location"].endswith("/login")

def test_configuracoes_com_login_mostra_dados_do_usuario(client, user_teste):
    autenticar(client, user_teste)

    entrar_configuracoes = client.get("/dashboard/configuracoes")

    assert b"teste@example.com" in entrar_configuracoes.data

# ---------- / (landing / redirecionamento) ----------

def test_index_sem_login_mostra_landing(client):
    entra_landing = client.get("/")

    assert entra_landing.status_code == 200
    assert b"Feito pra quem compartilha muitos links" in entra_landing.data

def test_index_com_login_redireciona_para_dashboard(client, user_teste):
    autenticar(client, user_teste)

    ser_redirecionado_para_dashboard = client.get("/")

    assert ser_redirecionado_para_dashboard.status_code == 302
    assert ser_redirecionado_para_dashboard.headers["Location"].endswith("/dashboard")

# ---------- /login e /callback/google ----------

def test_login_redireciona_para_google(client):
    entrar_login_redirecionamento = client.get("/login")

    assert entrar_login_redirecionamento.status_code == 302

def test_callback_google_cria_usuario_novo(client, app, monkeypatch):
    # Token falso exatamente no formato usado pelo callback:
    # token["userinfo"]["sub"], ["email"] e ["name"]
    token_falso = {
        "userinfo": {
            "sub": "google-123456",
            "email": "novo@gmail.com",
            "name": "Usuário Novo",
        }
    }

    # Substitui temporariamente authorize_access_token()
    # para não chamar o Google de verdade.
    monkeypatch.setattr(
        oauth.google,
        "authorize_access_token",
        lambda: token_falso,
    )

    resposta = client.get("/callback/google")

    # Deve redirecionar para /dashboard
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/dashboard")

    with app.app_context():
        # Verifica se o usuário foi criado com os dados do token
        usuario = User.query.filter_by(
            google_id="google-123456"
        ).first()

        assert usuario is not None
        assert usuario.email == "novo@gmail.com"
        assert usuario.name == "Usuário Novo"

        # Verifica se o user_id foi salvo na sessão
        with client.session_transaction() as sess:
            assert sess["user_id"] == usuario.id

def test_callback_google_reconhece_usuario_existente(
    client, app, user_teste, monkeypatch
):
    with app.app_context():
        # user_teste é o ID do usuário, não o objeto User
        usuario = db.session.get(User, user_teste)

        assert usuario is not None

        # Usa os mesmos dados do usuário já existente
        token_falso = {
            "userinfo": {
                "sub": usuario.google_id,
                "email": usuario.email,
                "name": usuario.name,
            }
        }

    # Mock do Google
    monkeypatch.setattr(
        oauth.google,
        "authorize_access_token",
        lambda: token_falso,
    )

    resposta = client.get("/callback/google")

    # Deve redirecionar para /dashboard
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/dashboard")

    with app.app_context():
        # Não deve criar um segundo usuário
        assert User.query.count() == 1

    # Verifica se o usuário existente foi colocado na sessão
    with client.session_transaction() as sess:
        assert sess["user_id"] == user_teste