from app import db
from app.models import Click, Link

UA_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1"
)
UA_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
UA_BOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


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


def test_pais_e_cidade_vem_dos_headers_da_vercel(client, app, user_teste):
    criar_link(app, user_teste, "col001")

    resposta = client.get(
        "/col001",
        headers={
            "x-vercel-ip-country": "br",
            "x-vercel-ip-city": "S%C3%A3o%20Paulo",
        },
    )

    assert resposta.status_code == 302
    with app.app_context():
        clique = Click.query.one()
        assert clique.pais == "BR"
        assert clique.cidade == "São Paulo"


def test_celular_e_navegador_pelo_user_agent(client, app, user_teste):
    criar_link(app, user_teste, "col002")

    client.get("/col002", headers={"User-Agent": UA_IPHONE})

    with app.app_context():
        clique = Click.query.one()
        assert clique.dispositivo == "celular"
        assert "Safari" in clique.navegador


def test_computador_e_navegador_pelo_user_agent(client, app, user_teste):
    criar_link(app, user_teste, "col003")

    client.get("/col003", headers={"User-Agent": UA_CHROME})

    with app.app_context():
        clique = Click.query.one()
        assert clique.dispositivo == "computador"
        assert clique.navegador == "Chrome"


def test_bot_e_marcado_como_bot(client, app, user_teste):
    criar_link(app, user_teste, "col004")

    client.get("/col004", headers={"User-Agent": UA_BOT})

    with app.app_context():
        assert Click.query.one().dispositivo == "bot"


def test_origem_guarda_so_o_dominio(client, app, user_teste):
    criar_link(app, user_teste, "col005")

    client.get(
        "/col005",
        headers={"Referer": "https://instagram.com/algum/caminho?x=1"},
    )

    with app.app_context():
        assert Click.query.one().origem == "instagram.com"


def test_origem_do_proprio_site_fica_vazia(client, app, user_teste):
    criar_link(app, user_teste, "col006")

    client.get("/col006", headers={"Referer": "http://localhost/dashboard"})

    with app.app_context():
        assert Click.query.one().origem is None


def test_sem_headers_salva_vazio_e_redireciona(client, app, user_teste):
    criar_link(app, user_teste, "col007")

    resposta = client.get("/col007")

    assert resposta.status_code == 302
    with app.app_context():
        clique = Click.query.one()
        assert clique.pais is None
        assert clique.cidade is None
        assert clique.origem is None


def test_user_agent_estranho_nao_quebra_o_redirect(client, app, user_teste):
    criar_link(app, user_teste, "col008")

    resposta = client.get("/col008", headers={"User-Agent": "lixo-@@@-###-???"})

    assert resposta.status_code == 302
    with app.app_context():
        assert Click.query.count() == 1