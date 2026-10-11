from datetime import timedelta

from app import db
from app.models import Click, ClickResumo, Link, RegistroAcesso, User, utcnow
from app.planos import PLANOS
from app.services.retencao import executar_retencao, total_cliques_por_link

GRATUITO = PLANOS["gratuito"]["historico_dias"]
PRO = PLANOS["pro"]["historico_dias"]


def criar_link_com_cliques(app, user_id, idades_em_dias, short_code="ret123"):
    with app.app_context():
        link = Link(
            original_url="https://example.com",
            short_code=short_code,
            user_id=user_id,
            is_active=True,
        )
        db.session.add(link)
        db.session.commit()

        for dias in idades_em_dias:
            db.session.add(
                Click(
                    link_id=link.id,
                    clicked_at=utcnow() - timedelta(days=dias),
                    user_agent="pytest",
                )
            )
        db.session.commit()
        return link.id


def definir_plano(app, user_id, plano, data_renovacao=None):
    with app.app_context():
        user = db.session.get(User, user_id)
        user.plano = plano
        user.data_renovacao = data_renovacao
        db.session.commit()


def total_resumo():
    return sum(r.total_cliques for r in ClickResumo.query.all())


def test_gratuito_perde_detalhe_apos_o_prazo(app, user_teste):
    criar_link_com_cliques(app, user_teste, [GRATUITO + 3, GRATUITO + 3, 1])

    with app.app_context():
        resultado = executar_retencao()

        assert resultado["por_plano"]["gratuito"] == 2
        assert Click.query.count() == 1
        assert total_resumo() == 2


def test_pro_mantem_detalhe_ate_o_limite_do_plano(app, user_teste):
    definir_plano(app, user_teste, "pro", utcnow() + timedelta(days=30))
    criar_link_com_cliques(app, user_teste, [PRO - 5, PRO + 5])

    with app.app_context():
        resultado = executar_retencao()

        assert resultado["por_plano"]["pro"] == 1
        assert Click.query.count() == 1
        assert total_resumo() == 1


def test_pro_vencido_ha_10_dias_ainda_tem_carencia(app, user_teste):
    definir_plano(app, user_teste, "pro", utcnow() - timedelta(days=10))
    criar_link_com_cliques(app, user_teste, [GRATUITO + 90])

    with app.app_context():
        executar_retencao()

        assert Click.query.count() == 1
        assert total_resumo() == 0


def test_pro_vencido_ha_40_dias_vira_gratuito(app, user_teste):
    definir_plano(app, user_teste, "pro", utcnow() - timedelta(days=40))
    criar_link_com_cliques(app, user_teste, [GRATUITO + 90])

    with app.app_context():
        executar_retencao()

        assert Click.query.count() == 0
        assert total_resumo() == 1


def test_registro_de_acesso_de_gratuito_sobrevive_a_retencao_do_click(app, user_teste):
    link_id = criar_link_com_cliques(app, user_teste, [GRATUITO + 3])

    with app.app_context():
        db.session.add(
            RegistroAcesso(
                link_id=link_id,
                acessado_em=utcnow() - timedelta(days=GRATUITO + 3),
                ip_cifrado="token-qualquer",
            )
        )
        db.session.commit()

        executar_retencao()

        assert Click.query.count() == 0
        assert RegistroAcesso.query.count() == 1


def test_registro_de_acesso_e_apagado_apos_o_prazo(app, user_teste):
    app.config["IP_RETENCAO_DIAS"] = 190
    link_id = criar_link_com_cliques(app, user_teste, [])

    with app.app_context():
        for dias in (200, 100):
            db.session.add(
                RegistroAcesso(
                    link_id=link_id,
                    acessado_em=utcnow() - timedelta(days=dias),
                    ip_cifrado="token-qualquer",
                )
            )
        db.session.commit()

        resultado = executar_retencao()

        assert resultado["registros_acesso_apagados"] == 1
        assert RegistroAcesso.query.count() == 1


def test_retencao_nao_duplica_ao_rodar_duas_vezes(app, user_teste):
    criar_link_com_cliques(app, user_teste, [GRATUITO + 3, GRATUITO + 3, 1])

    with app.app_context():
        executar_retencao()
        segundo = executar_retencao()

        assert segundo["cliques_arquivados"] == 0
        assert total_resumo() == 2


def test_totais_continuam_somando_recentes_e_antigos(app, user_teste):
    link_id = criar_link_com_cliques(app, user_teste, [GRATUITO + 3, GRATUITO + 3, 1])

    with app.app_context():
        executar_retencao()

        assert total_cliques_por_link([link_id])[link_id] == 3


def test_rota_retencao_sem_segredo_retorna_401(client, app):
    app.config["CRON_SECRET"] = "segredo-teste"

    resposta = client.get("/manutencao/retencao")

    assert resposta.status_code == 401


def test_rota_retencao_com_segredo_retorna_200(client, app):
    app.config["CRON_SECRET"] = "segredo-teste"

    resposta = client.get(
        "/manutencao/retencao",
        headers={"Authorization": "Bearer segredo-teste"},
    )

    assert resposta.status_code == 200
    assert "cliques_arquivados" in resposta.get_json()