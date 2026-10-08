from collections import Counter
from datetime import timedelta

from flask import current_app
from sqlalchemy import func

from app import db
from app.models import Click, ClickResumo, utcnow

TAMANHO_LOTE = 5000
MAX_LOTES = 20
TAMANHO_DELETE = 500


def calcular_data_limite():
    dias = current_app.config.get("CLICK_RETENTION_DAYS", 365)
    return utcnow() - timedelta(days=dias)


def _processar_lote(data_limite):
    """Agrega e apaga um lote de cliques antigos. Não faz commit.
    Retorna a quantidade de cliques processados."""
    linhas = (
        db.session.query(Click.id, Click.link_id, Click.clicked_at)
        .filter(Click.clicked_at < data_limite)
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


def executar_retencao():
    """Roda vários lotes numa única transação.
    Se algo falhar, nada é apagado nem agregado."""
    data_limite = calcular_data_limite()
    total = 0
    try:
        for _ in range(MAX_LOTES):
            processados = _processar_lote(data_limite)
            if processados == 0:
                break
            total += processados
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return {"cliques_arquivados": total, "limite": data_limite.isoformat()}


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