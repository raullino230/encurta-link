from flask import Blueprint, request, current_app, session, abort
from app.models import db, Link
from app.utils import EncurtadorBase62
from app import limiter
from sqlalchemy import func
from urllib.parse import urlparse

links_bp = Blueprint("links", __name__)

limite_plano_gratis = 10


@links_bp.route("/links", methods=["POST", "GET"])
@limiter.limit(
    "10/minute",
    methods=["POST"]
)
def create_link():
    if "user_id" not in session:
        abort(401)

    if request.method == "GET":
        return "Essa é a pagina da criação de urls curtas"

    links_pertencem_usuario = (
        db.session.query(func.count(Link.id))
        .filter(Link.user_id == session["user_id"])
        .scalar()
    )

    if links_pertencem_usuario >= limite_plano_gratis:
        abort(403, description="Você atingiu o limite de links do seu plano.")

    dados = request.get_json(silent=True)
    url = dados.get("original_url") if isinstance(dados, dict) else None

    if not isinstance(url, str) or not url.strip():
        abort(400, description="Envie uma URL para encurtar.")

    url = url.strip()

    if len(url) > current_app.config["LIMITE_TAMANHO_URL"]:
        abort(400, description="A URL é grande demais.")

    url_partes = urlparse(url)

    if url_partes.scheme not in ("http", "https") or not url_partes.netloc:
        abort(400, description="Envie uma URL válida, começando com http ou https.")

    encurtador = EncurtadorBase62()
    link_model = Link(original_url=url, user_id=session["user_id"])

    while True:
        codigo = encurtador.gerar_codigo_aleatorio(6)

        verificacao = db.session.query(Link).filter(Link.short_code == codigo).first()

        link_model.short_code = codigo

        if verificacao is None:
            break

    db.session.add(link_model)
    db.session.commit()

    return {
        "short_url": current_app.config["BASE_URL"] + link_model.short_code
    }