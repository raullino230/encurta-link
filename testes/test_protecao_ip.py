from cryptography.fernet import Fernet

from app import db
from app.models import Click, Link, RegistroAcesso
from app.services.protecao_ip import (
    cifrar_ip,
    decifrar_ip,
    hash_visitante,
    parece_cifrado,
)

IP = "200.100.50.25"


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
        return link.id


# ---------- cifra ----------

def test_cifra_e_decifra_voltam_ao_ip_original(app):
    token = cifrar_ip(IP)

    assert token
    assert token != IP
    assert IP not in token
    assert decifrar_ip(token) == IP


def test_chave_ausente_devolve_none(app):
    app.config["IP_CRIPTO_CHAVE"] = None

    assert cifrar_ip(IP) is None
    assert decifrar_ip("qualquer-coisa") is None


def test_chave_com_formato_invalido_devolve_none(app):
    app.config["IP_CRIPTO_CHAVE"] = "abc"

    assert cifrar_ip(IP) is None


def test_ip_cifrado_com_outra_chave_nao_decifra(app):
    token = cifrar_ip(IP)
    app.config["IP_CRIPTO_CHAVE"] = Fernet.generate_key().decode()

    assert decifrar_ip(token) is None


def test_decifrar_token_vazio_devolve_none(app):
    assert decifrar_ip(None) is None
    assert decifrar_ip("") is None


# ---------- hash ----------

def test_hash_e_estavel_para_o_mesmo_ip(app):
    assert hash_visitante(IP) == hash_visitante(IP)
    assert len(hash_visitante(IP)) == 32


def test_hash_e_diferente_para_ips_diferentes(app):
    assert hash_visitante("200.100.50.25") != hash_visitante("200.100.50.26")


def test_ipv6_do_mesmo_prefixo_gera_o_mesmo_hash(app):
    assert hash_visitante("2001:db8:abcd:1234::1") == hash_visitante("2001:db8:abcd:1234::ffff")


def test_hash_de_texto_que_nao_e_ip_devolve_none(app):
    assert hash_visitante("abc") is None
    assert hash_visitante(None) is None


def test_hash_sem_segredo_devolve_none(app):
    app.config["HASH_SEGREDO"] = None

    assert hash_visitante(IP) is None


def test_segredos_diferentes_geram_hashes_diferentes(app):
    primeiro = hash_visitante(IP)
    app.config["HASH_SEGREDO"] = "outro-segredo"

    assert hash_visitante(IP) != primeiro


# ---------- parece_cifrado ----------

def test_parece_cifrado(app):
    assert parece_cifrado(cifrar_ip(IP)) is True
    assert parece_cifrado(IP) is False
    assert parece_cifrado(None) is False
    assert parece_cifrado("") is False


# ---------- no clique ----------

def test_clique_cria_registro_de_acesso_com_ip_cifrado(client, app, user_teste):
    criar_link(app, user_teste, "ip0001")

    client.get("/ip0001", headers={"x-forwarded-for": f"{IP}, 10.0.0.1"})

    with app.app_context():
        registro = RegistroAcesso.query.one()
        assert registro.ip_cifrado != IP
        assert decifrar_ip(registro.ip_cifrado) == IP

        clique = Click.query.one()
        assert clique.visitante_hash == hash_visitante(IP)

        assert not hasattr(Click, "ip_address")


def test_sem_chave_nao_grava_ip_e_o_redirect_continua(client, app, user_teste):
    criar_link(app, user_teste, "ip0002")
    app.config["IP_CRIPTO_CHAVE"] = None

    resposta = client.get("/ip0002", headers={"x-forwarded-for": IP})

    assert resposta.status_code == 302
    with app.app_context():
        assert RegistroAcesso.query.count() == 0
        assert Click.query.count() == 1


# ---------- comando proteger-ips ---------


def test_proteger_ips_falha_sem_chave(app, user_teste):
    app.config["IP_CRIPTO_CHAVE"] = None

    resultado = app.test_cli_runner().invoke(args=["proteger-ips"])

    assert resultado.exit_code != 0


# ---------- o IP não aparece em tela ----------

def test_ip_nao_aparece_no_dashboard(client, app, user_teste):
    criar_link(app, user_teste, "ip0004")
    client.get("/ip0004", headers={"x-forwarded-for": IP})
    autenticar(client, user_teste)

    for rota in ("/dashboard", "/dashboard/analytics", "/dashboard/configuracoes"):
        resposta = client.get(rota)
        assert IP.encode() not in resposta.data