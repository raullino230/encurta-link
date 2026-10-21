from datetime import datetime, timedelta, timezone
from flask import Blueprint, session, redirect, request, abort
from sqlalchemy import func
from fasthtml.common import to_xml
from app.models import db, Link, Click, User
from app.frontend.componentes_landing import Layout
from app.frontend.componentes_dashboard import MeusLinksPage, AnalyticsPage, ConfiguracoesPage
from app.services.retencao import total_cliques_por_link
from app.planos import limite_links, regras_do_plano, obter_plano
from app.services.analytics import *

dashboard_bp = Blueprint("dashboard", __name__)



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

    user = db.session.get(User, session["user_id"])
    if user is None:
        session.clear()
        return redirect("/login")

    valor = request.args.get("periodo")

    dias = normalizar_periodo(valor, user)
    user_pro = user.is_pro
    link_id = None
    link_atual = None
    if user_pro:
        codigo = request.args.get("link")
        if codigo:
            link = (
                db.session.query(Link)
                .filter(Link.user_id == user.id)
                .filter(Link.short_code == codigo)
                .first()
            )
            if link is None:
                abort(404)
            link_id = link.id
            link_atual = link.short_code

    dados_resumo = resumo(user.id, dias, link_id)
    por_dia = serie_cliques(user.id, dias, link_id)
    mais_clicados = links_mais_clicados(user.id, dias, link_id)
    periodos_liberados = periodos_disponiveis(user)

    horas = None
    rankings = {}

    seletor_de_link = []

    if user_pro:
        horas = cliques_por_hora(user.id, dias, link_id)

        for categoria in COLUNAS_RANKING:
            rankings[categoria] = ranking(categoria, user.id, dias, link_id)

        linhas = (
            db.session.query(Link.short_code)
            .filter(Link.user_id == user.id)
            .order_by(Link.short_code)
            .all()
        )

        for (codigo_do_link,) in linhas:
            seletor_de_link.append(codigo_do_link)

    pagina = AnalyticsPage(
        periodo = dias,
        periodos_liberados = periodos_liberados,
        resumo = dados_resumo,
        serie = por_dia,
        top_links = mais_clicados,
        is_pro = user_pro,
        link_atual = link_atual,
        links_do_usuario = seletor_de_link,
        horas = horas,
        rankings = rankings,
    )
    return to_xml(Layout(pagina))


@dashboard_bp.route("/dashboard/configuracoes")
def ver_configuracoes():
    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    links_usados = (
        db.session.query(func.count(Link.id))
        .filter(Link.user_id == user.id)
        .scalar()
    ) or 0

    pagina = ConfiguracoesPage(
        usuario={"name": user.name, "email": user.email},
        links_usados=links_usados,
        limite_plano=limite_links(user),
        plano_nome=regras_do_plano(user)["nome"],
        is_pro=user.is_pro,
    )
    return to_xml(Layout(pagina))