from datetime import timedelta

import pytest

from app import db
from app.models import Click, Link, RegistroAcesso, User, utcnow
from app.services.analytics import (
    cliques_por_hora,
    links_mais_clicados,
    normalizar_periodo,
    periodos_disponiveis,
    ranking,
    resumo,
    serie_cliques,
)


# ---------- ajudantes ----------

def autenticar(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def tornar_pro(app, user_id):
    with app.app_context():
        user = db.session.get(User, user_id)
        user.plano = "pro"
        user.data_renovacao = utcnow() + timedelta(days=30)
        db.session.commit()


def criar_outro_usuario(app):
    with app.app_context():
        user = User(
            google_id="google-outro",
            name="Outro Usuario",
            email="outro@example.com",
        )
        db.session.add(user)
        db.session.commit()
        return user.id


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


def criar_clique_em(app, link_id, quando, **dados):
    with app.app_context():
        db.session.add(
            Click(link_id=link_id, clicked_at=quando, user_agent="pytest", **dados)
        )
        db.session.commit()


def criar_clique(app, link_id, dias_atras=0, **dados):
    criar_clique_em(app, link_id, utcnow() - timedelta(days=dias_atras), **dados)


# ---------- períodos ----------

def test_periodos_do_gratuito_so_tem_7_dias(app, user_teste):
    with app.app_context():
        user = db.session.get(User, user_teste)

        assert periodos_disponiveis(user) == [7]


def test_periodos_do_pro_vao_ate_um_ano(app, user_teste):
    tornar_pro(app, user_teste)

    with app.app_context():
        user = db.session.get(User, user_teste)

        assert periodos_disponiveis(user) == [7, 30, 90, 365]


def test_normalizar_periodo_gratuito_ignora_periodo_maior(app, user_teste):
    with app.app_context():
        user = db.session.get(User, user_teste)

        assert normalizar_periodo("30", user) == 7
        assert normalizar_periodo("365", user) == 7


def test_normalizar_periodo_pro_aceita_os_periodos_validos(app, user_teste):
    tornar_pro(app, user_teste)

    with app.app_context():
        user = db.session.get(User, user_teste)

        for valor, esperado in (("7", 7), ("30", 30), ("90", 90), ("365", 365)):
            assert normalizar_periodo(valor, user) == esperado


def test_normalizar_periodo_invalido_volta_para_7(app, user_teste):
    tornar_pro(app, user_teste)

    with app.app_context():
        user = db.session.get(User, user_teste)

        for valor in (None, "", "abc", "-5", "0", "15", "30.5"):
            assert normalizar_periodo(valor, user) == 7


# ---------- resumo ----------

def test_resumo_conta_so_o_periodo(app, user_teste):
    link_id = criar_link(app, user_teste, "res001")
    criar_clique(app, link_id, dias_atras=1)
    criar_clique(app, link_id, dias_atras=2)
    criar_clique(app, link_id, dias_atras=20)

    with app.app_context():
        assert resumo(user_teste, 7)["total_cliques"] == 2
        assert resumo(user_teste, 30)["total_cliques"] == 3


def test_resumo_media_por_dia(app, user_teste):
    link_id = criar_link(app, user_teste, "res002")
    for _ in range(14):
        criar_clique(app, link_id, dias_atras=1)

    with app.app_context():
        assert resumo(user_teste, 7)["media_dia"] == 2.0


def test_resumo_conta_visitantes_unicos_ignorando_vazios(app, user_teste):
    link_id = criar_link(app, user_teste, "res003")
    for visitante in ("aaa", "aaa", "bbb", None):
        criar_clique(app, link_id, dias_atras=1, visitante_hash=visitante)

    with app.app_context():
        assert resumo(user_teste, 7)["visitantes_unicos"] == 2


def test_resumo_conta_so_links_ativos(app, user_teste):
    criar_link(app, user_teste, "ativo1")
    criar_link(app, user_teste, "ativo2")
    criar_link(app, user_teste, "inativ1", ativo=False)

    with app.app_context():
        assert resumo(user_teste, 7)["links_ativos"] == 2


def test_resumo_nao_conta_cliques_de_outro_usuario(app, user_teste):
    outro = criar_outro_usuario(app)
    link_outro = criar_link(app, outro, "outro01")
    criar_clique(app, link_outro, dias_atras=1)

    with app.app_context():
        assert resumo(user_teste, 7)["total_cliques"] == 0


def test_resumo_filtra_por_link(app, user_teste):
    link_a = criar_link(app, user_teste, "fil001")
    link_b = criar_link(app, user_teste, "fil002")
    criar_clique(app, link_a, dias_atras=1)
    criar_clique(app, link_a, dias_atras=1)
    criar_clique(app, link_b, dias_atras=1)

    with app.app_context():
        assert resumo(user_teste, 7, link_id=link_a)["total_cliques"] == 2
        assert resumo(user_teste, 7)["total_cliques"] == 3


# ---------- série ----------

def test_serie_de_7_dias_tem_7_pontos_e_soma_os_cliques(app, user_teste):
    link_id = criar_link(app, user_teste, "ser001")
    criar_clique(app, link_id, dias_atras=0)
    criar_clique(app, link_id, dias_atras=3)
    criar_clique(app, link_id, dias_atras=3)

    with app.app_context():
        serie = serie_cliques(user_teste, 7)

        assert len(serie) == 7
        assert sum(total for _, total in serie) == 3
        assert serie[-1][1] == 1


def test_serie_de_30_dias_tem_30_pontos(app, user_teste):
    with app.app_context():
        assert len(serie_cliques(user_teste, 30)) == 30


def test_serie_longa_soma_todos_os_cliques_do_periodo(app, user_teste):
    link_id = criar_link(app, user_teste, "ser002")
    criar_clique(app, link_id, dias_atras=1)
    criar_clique(app, link_id, dias_atras=40)
    criar_clique(app, link_id, dias_atras=200)

    with app.app_context():
        assert sum(total for _, total in serie_cliques(user_teste, 90)) == 2
        assert sum(total for _, total in serie_cliques(user_teste, 365)) == 3


# ---------- horários ----------

def test_horarios_convertem_para_o_horario_de_brasilia(app, user_teste):
    link_id = criar_link(app, user_teste, "hor001")
    base = (utcnow() - timedelta(days=1)).replace(
        hour=15, minute=0, second=0, microsecond=0
    )
    criar_clique_em(app, link_id, base)

    with app.app_context():
        horas = cliques_por_hora(user_teste, 7)

        assert len(horas) == 24
        assert horas[12] == 1
        assert sum(horas) == 1


def test_horarios_de_madrugada_utc_viram_noite_no_dia_anterior(app, user_teste):
    link_id = criar_link(app, user_teste, "hor002")
    base = (utcnow() - timedelta(days=1)).replace(
        hour=2, minute=0, second=0, microsecond=0
    )
    criar_clique_em(app, link_id, base)

    with app.app_context():
        horas = cliques_por_hora(user_teste, 7)

        assert horas[23] == 1


# ---------- rankings ----------

def test_ranking_conta_e_calcula_percentual(app, user_teste):
    link_id = criar_link(app, user_teste, "ran001")
    for pais in ("BR", "BR", "BR", "US", None):
        criar_clique(app, link_id, dias_atras=1, pais=pais)

    with app.app_context():
        resultado = ranking("pais", user_teste, 7)
        por_rotulo = {rotulo: (total, perc) for rotulo, total, perc in resultado}

        assert resultado[0][0] == "BR"
        assert por_rotulo["BR"] == (3, 60)
        assert por_rotulo["US"] == (1, 20)
        assert por_rotulo["Desconhecido"] == (1, 20)


def test_ranking_de_origem_chama_o_vazio_de_direto(app, user_teste):
    link_id = criar_link(app, user_teste, "ran002")
    criar_clique(app, link_id, dias_atras=1, origem="instagram.com")
    criar_clique(app, link_id, dias_atras=1, origem=None)

    with app.app_context():
        rotulos = [rotulo for rotulo, _, _ in ranking("origem", user_teste, 7)]

        assert "instagram.com" in rotulos
        assert "Direto" in rotulos


def test_ranking_respeita_o_limite(app, user_teste):
    link_id = criar_link(app, user_teste, "ran003")
    for numero in range(12):
        criar_clique(app, link_id, dias_atras=1, cidade=f"Cidade{numero}")

    with app.app_context():
        assert len(ranking("cidade", user_teste, 7, limite=10)) == 10


def test_ranking_recusa_coluna_fora_da_lista(app, user_teste):
    with app.app_context():
        with pytest.raises(ValueError):
            ranking("user_agent", user_teste, 7)


def test_ranking_nao_conta_cliques_de_outro_usuario(app, user_teste):
    outro = criar_outro_usuario(app)
    link_outro = criar_link(app, outro, "outro02")
    criar_clique(app, link_outro, dias_atras=1, pais="JP")

    with app.app_context():
        assert ranking("pais", user_teste, 7) == []


# ---------- links mais clicados ----------

def test_links_mais_clicados_ordena_e_so_conta_do_usuario(app, user_teste):
    link_a = criar_link(app, user_teste, "top001")
    link_b = criar_link(app, user_teste, "top002")
    outro = criar_outro_usuario(app)
    link_outro = criar_link(app, outro, "outro03")

    for _ in range(3):
        criar_clique(app, link_a, dias_atras=1)
    criar_clique(app, link_b, dias_atras=1)
    for _ in range(5):
        criar_clique(app, link_outro, dias_atras=1)

    with app.app_context():
        resultado = [tuple(linha) for linha in links_mais_clicados(user_teste, 7)]

        assert resultado[0] == ("top001", 3)
        assert ("top002", 1) in resultado
        assert all(codigo != "outro03" for codigo, _ in resultado)


def test_links_mais_clicados_ignora_links_sem_clique_no_periodo(app, user_teste):
    link_id = criar_link(app, user_teste, "top003")
    criar_clique(app, link_id, dias_atras=20)

    with app.app_context():
        assert links_mais_clicados(user_teste, 7) == []


# ---------- página: gratuito ----------

def test_analytics_gratuito_mostra_o_basico_e_bloqueia_o_avancado(client, app, user_teste):
    link_id = criar_link(app, user_teste, "gra001")
    criar_clique(
        app, link_id, dias_atras=1,
        cidade="Cidadelandia", origem="origem-teste.com",
    )
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics")

    assert resposta.status_code == 200
    assert b"gra001" in resposta.data
    assert "Disponível no Pro".encode() in resposta.data
    assert b"Cidadelandia" not in resposta.data
    assert b"origem-teste.com" not in resposta.data


def test_analytics_gratuito_ignora_periodo_maior(client, app, user_teste):
    link_id = criar_link(app, user_teste, "gra002")
    criar_clique(app, link_id, dias_atras=20)
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics?periodo=30")

    assert resposta.status_code == 200
    assert b"gra002" not in resposta.data


def test_analytics_gratuito_ignora_filtro_de_link(client, user_teste):
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics?link=qualquer")

    assert resposta.status_code == 200


# ---------- página: Pro ----------

def test_analytics_pro_mostra_os_rankings(client, app, user_teste):
    tornar_pro(app, user_teste)
    link_id = criar_link(app, user_teste, "pro001")
    criar_clique(
        app, link_id, dias_atras=1,
        pais="BR", cidade="Cidadelandia", dispositivo="celular",
        navegador="NavegadorTeste", origem="origem-teste.com",
    )
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics")

    assert resposta.status_code == 200
    assert b"Cidadelandia" in resposta.data
    assert b"NavegadorTeste" in resposta.data
    assert b"origem-teste.com" in resposta.data
    assert "Disponível no Pro".encode() not in resposta.data


def test_analytics_pro_mostra_desconhecido_e_direto_para_cliques_sem_dados(client, app, user_teste):
    tornar_pro(app, user_teste)
    link_id = criar_link(app, user_teste, "pro002")
    criar_clique(app, link_id, dias_atras=1)
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics")

    assert b"Desconhecido" in resposta.data
    assert b"Direto" in resposta.data


def test_analytics_pro_respeita_o_periodo_escolhido(client, app, user_teste):
    tornar_pro(app, user_teste)
    link_id = criar_link(app, user_teste, "pro003")
    criar_clique(app, link_id, dias_atras=1, cidade="Recentelandia")
    criar_clique(app, link_id, dias_atras=20, cidade="Antigolandia")
    autenticar(client, user_teste)

    sete = client.get("/dashboard/analytics?periodo=7")
    trinta = client.get("/dashboard/analytics?periodo=30")

    assert b"Recentelandia" in sete.data
    assert b"Antigolandia" not in sete.data
    assert b"Antigolandia" in trinta.data


def test_analytics_pro_filtra_por_link(client, app, user_teste):
    tornar_pro(app, user_teste)
    link_a = criar_link(app, user_teste, "fa0001")
    link_b = criar_link(app, user_teste, "fb0001")
    criar_clique(app, link_a, dias_atras=1, cidade="CidadeA")
    criar_clique(app, link_b, dias_atras=1, cidade="CidadeB")
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics?link=fa0001")

    assert resposta.status_code == 200
    assert b"CidadeA" in resposta.data
    assert b"CidadeB" not in resposta.data


def test_analytics_pro_link_de_outro_usuario_retorna_404(client, app, user_teste):
    tornar_pro(app, user_teste)
    outro = criar_outro_usuario(app)
    criar_link(app, outro, "alheio1")
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics?link=alheio1")

    assert resposta.status_code == 404


def test_analytics_pro_link_inexistente_retorna_404(client, app, user_teste):
    tornar_pro(app, user_teste)
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics?link=naoexiste")

    assert resposta.status_code == 404


def test_analytics_nao_mostra_dados_de_outro_usuario(client, app, user_teste):
    tornar_pro(app, user_teste)
    outro = criar_outro_usuario(app)
    link_outro = criar_link(app, outro, "alheio2")
    criar_clique(app, link_outro, dias_atras=1, cidade="Alheialandia")
    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics")

    assert b"Alheialandia" not in resposta.data
    assert b"alheio2" not in resposta.data


# ---------- página: geral ----------

def test_analytics_periodo_invalido_nao_quebra(client, user_teste):
    autenticar(client, user_teste)

    for valor in ("abc", "-1", "9999", ""):
        resposta = client.get(f"/dashboard/analytics?periodo={valor}")

        assert resposta.status_code == 200


def test_analytics_com_parametros_sem_login_redireciona(client):
    resposta = client.get("/dashboard/analytics?periodo=30&link=x")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")


def test_analytics_nao_mostra_ip(client, app, user_teste):
    tornar_pro(app, user_teste)
    link_id = criar_link(app, user_teste, "pro004")
    criar_clique(app, link_id, dias_atras=1)

    with app.app_context():
        db.session.add(
            RegistroAcesso(
                link_id=link_id,
                acessado_em=utcnow(),
                ip_cifrado="gAAAAA-token-de-teste",
            )
        )
        db.session.commit()

    autenticar(client, user_teste)

    resposta = client.get("/dashboard/analytics")

    assert b"gAAAAA-token-de-teste" not in resposta.data