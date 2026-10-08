from datetime import datetime, timedelta, timezone
from flask import Blueprint, session, redirect
from sqlalchemy import func
from fasthtml.common import to_xml
from app.models import db, Link, Click, User
from app.frontend.componentes_landing import Layout
from app.frontend.componentes_dashboard import MeusLinksPage, AnalyticsPage, ConfiguracoesPage
from app.services.retencao import total_cliques_por_link

dashboard_bp = Blueprint("dashboard", __name__)

LIMITE_PLANO_GRATIS = 10  # mesmo valor de links.py — vale centralizar isso em config.py depois
DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


@dashboard_bp.route("/dashboard")
def ver_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    resultados = (
        db.session.query(Link, func.count(Click.id).label("total_cliques"))
        .outerjoin(Click)
        .filter(Link.user_id == session["user_id"])
        .group_by(Link.id)
        .all()
    )

    totais = total_cliques_por_link([link.id for link, _ in resultados])

    links_formatados = []
    total_cliques_geral = 0

    for link, _ in resultados:        
        total_cliques = totais.get(link.id, 0)
        links_formatados.append({
            "short_code": link.short_code,
            "original_url": link.original_url,
            "total_cliques": total_cliques,
            "created_at": link.created_at.strftime("%d %b"),
            "is_active": link.is_active,
        })
        total_cliques_geral += total_cliques

    pagina = MeusLinksPage(
        links=links_formatados,
        total_links=len(links_formatados),
        total_cliques=total_cliques_geral,
    )

    return to_xml(Layout(pagina))


@dashboard_bp.route("/dashboard/analytics")
def ver_analytics():
    if "user_id" not in session:
        return redirect("/login")

    agora = datetime.now(timezone.utc)
    sete_dias_atras = agora - timedelta(days=7)

    links_do_usuario = db.session.query(Link.id).filter(Link.user_id == session["user_id"])

    cliques_7_dias = (
        db.session.query(func.count(Click.id))
        .filter(Click.link_id.in_(links_do_usuario))
        .filter(Click.clicked_at >= sete_dias_atras)
        .scalar()
    ) or 0

    links_ativos = (
        db.session.query(func.count(Link.id))
        .filter(Link.user_id == session["user_id"], Link.is_active == True)
        .scalar()
    ) or 0

    media_dia = round(cliques_7_dias / 7, 1)

    # agrupa cliques por dia (últimos 7 dias)
    resultado_datas = (
        db.session.query(func.date(Click.clicked_at), func.count(Click.id))
        .filter(Click.link_id.in_(links_do_usuario))
        .filter(Click.clicked_at >= sete_dias_atras)
        .group_by(func.date(Click.clicked_at))
        .all()
    )
    cliques_por_data = {data: total for data, total in resultado_datas}
    maior_valor = max(cliques_por_data.values()) if cliques_por_data else 1

    cliques_por_dia = []
    for i in range(6, -1, -1):
        dia = (agora - timedelta(days=i)).date()
        total = cliques_por_data.get(dia, 0)
        altura = int((total / maior_valor) * 100) if maior_valor else 0
        cliques_por_dia.append((DIAS_SEMANA[dia.weekday()], altura))

    # top 5 links mais clicados
    links_usuario = (
        db.session.query(Link.id, Link.short_code)
        .filter(Link.user_id == session["user_id"])
        .all()
    )
    totais = total_cliques_por_link([l.id for l in links_usuario])

    top_links = sorted(
        [(l.short_code, totais.get(l.id, 0)) for l in links_usuario],
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    pagina = AnalyticsPage(
        cliques_7_dias=cliques_7_dias,
        links_ativos=links_ativos,
        media_dia=media_dia,
        cliques_por_dia=cliques_por_dia,
        top_links=list(top_links),
    )
    return to_xml(Layout(pagina))


@dashboard_bp.route("/dashboard/configuracoes")
def ver_configuracoes():
    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    links_usados = (
        db.session.query(func.count(Link.id))
        .filter(Link.user_id == session["user_id"])
        .scalar()
    ) or 0

    pagina = ConfiguracoesPage(
        usuario={"name": user.name, "email": user.email},
        links_usados=links_usados,
        limite_plano=LIMITE_PLANO_GRATIS,  # sem plano Pro real ainda, fica fixo por enquanto
    )
    return to_xml(Layout(pagina))