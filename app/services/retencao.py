from collections import Counter
from datetime import timedelta

from flask import current_app
from sqlalchemy import and_, func, not_, or_, select

from app import db
from app.models import Click, ClickResumo, Link, RegistroAcesso, User, utcnow
from app.planos import PLANOS

TAMANHO_LOTE = 5000
MAX_LOTES = 20
TAMANHO_DELETE = 500
DIAS_CARENCIA_PRO = 30


def _links_por_plano(pro):
    """Ids dos links cujo dono está no plano pedido.
    "Pro" aqui inclui a carência: Pro vencido há até 30 dias ainda conta como Pro."""
    corte = utcnow() - timedelta(days=DIAS_CARENCIA_PRO)

    dono_pro = and_(
        User.plano == "pro",
        User.data_renovacao.is_not(None),
        User.data_renovacao > corte,
    )

    consulta = (
        select(Link.id)
        .select_from(Link)
        .outerjoin(User, Link.user_id == User.id)
    )

    if pro:
        return consulta.where(dono_pro)

    return consulta.where(or_(User.id.is_(None), not_(dono_pro)))


def _processar_lote(data_limite, links_do_plano):
    """Agrega e apaga um lote de cliques antigos. Não faz commit.
    Devolve quantos cliques foram processados."""
    linhas = (
        db.session.query(Click.id, Click.link_id, Click.clicked_at)
        .filter(Click.clicked_at < data_limite, Click.link_id.in_(links_do_plano))
        .order_by(Click.clicked_at)
        .limit(TAMANHO_LOTE)
        .all()
    )
    if not linhas:
        return 0

    contagem = Counter((l.link_id, l.clicked_at.date()) for l in linhas)

    for (link_id, dia), qtd in contagem.items():
        resumo = ClickResumo.query.filter_by(link_id=link_id, data=dia).first()
        if resumo:
            resumo.total_cliques += qtd
        else:
            db.session.add(
                ClickResumo(link_id=link_id, data=dia, total_cliques=qtd)
            )

    ids = [l.id for l in linhas]
    for i in range(0, len(ids), TAMANHO_DELETE):
        parte = ids[i:i + TAMANHO_DELETE]
        Click.query.filter(Click.id.in_(parte)).delete(synchronize_session=False)

    db.session.flush()
    return len(linhas)


def apagar_registros_acesso_antigos():
    """Apaga os registros de acesso (IP cifrado) mais antigos que IP_RETENCAO_DIAS.
    Não faz commit."""
    dias = current_app.config.get("IP_RETENCAO_DIAS", 190)
    limite = utcnow() - timedelta(days=dias)

    return (
        RegistroAcesso.query
        .filter(RegistroAcesso.acessado_em < limite)
        .delete(synchronize_session=False)
    )


def executar_retencao():
    """Tudo numa única transação: se algo falhar, nada é apagado nem agregado."""
    total = 0
    por_plano = {}

    try:
        for nome, pro in (("gratuito", False), ("pro", True)):
            limite = utcnow() - timedelta(days=PLANOS[nome]["historico_dias"])
            links_do_plano = _links_por_plano(pro)

            arquivados = 0
            for _ in range(MAX_LOTES):
                processados = _processar_lote(limite, links_do_plano)
                if processados == 0:
                    break
                arquivados += processados

            por_plano[nome] = arquivados
            total += arquivados

        apagados = apagar_registros_acesso_antigos()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {
        "cliques_arquivados": total,
        "por_plano": por_plano,
        "registros_acesso_apagados": apagados,
    }


def total_cliques_por_link(link_ids):
    """Soma cliques recentes (Click) + antigos (ClickResumo) por link."""
    if not link_ids:
        return {}

    recentes = dict(
        db.session.query(Click.link_id, func.count(Click.id))
        .filter(Click.link_id.in_(link_ids))
        .group_by(Click.link_id)
        .all()
    )
    antigos = dict(
        db.session.query(ClickResumo.link_id, func.sum(ClickResumo.total_cliques))
        .filter(ClickResumo.link_id.in_(link_ids))
        .group_by(ClickResumo.link_id)
        .all()
    )
    return {
        lid: recentes.get(lid, 0) + int(antigos.get(lid, 0))
        for lid in link_ids
    }