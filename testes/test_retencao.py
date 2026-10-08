from datetime import timedelta

from app import db
from app.models import Click, ClickResumo, Link, utcnow
from app.services.retencao import executar_retencao


def criar_link_com_cliques(app, user_id, idades_em_dias):
    with app.app_context():
        link = Link(
            original_url="https://example.com",
            short_code="ret123",
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
                    ip_address="127.0.0.1",
                    user_agent="pytest",
                )
            )
        db.session.commit()
        return link.id


def test_retencao_agrega_e_apaga_cliques_antigos(app, user_teste):
    app.config["CLICK_RETENTION_DAYS"] = 30
    link_id = criar_link_com_cliques(app, user_teste, [40, 40, 5])

    with app.app_context():
        resultado = executar_retencao()

        assert resultado["cliques_arquivados"] == 2
        assert Click.query.count() == 1

        total_resumo = sum(r.total_cliques for r in ClickResumo.query.all())
        assert total_resumo == 2


def test_retencao_nao_duplica_ao_rodar_duas_vezes(app, user_teste):
    app.config["CLICK_RETENTION_DAYS"] = 30
    criar_link_com_cliques(app, user_teste, [40, 40, 5])

    with app.app_context():
        executar_retencao()
        segundo = executar_retencao()

        assert segundo["cliques_arquivados"] == 0
        assert sum(r.total_cliques for r in ClickResumo.query.all()) == 2


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