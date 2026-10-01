from flask import Blueprint, request, current_app, session
from app.models import db, Link
from app.utils import EncurtadorBase62
from app import limiter
from sqlalchemy import func
from urllib.parse import urlparse

links_bp = Blueprint("links", __name__)

limite_plano_gratis = 10

@links_bp.route("/links", methods = ["POST", "GET"])
@limiter.limit(
    "10/minute",
    methods = ["POST"]
)
def create_link():
    if "user_id" not in session:
        return ("Você precisa estar logado", 401)

    if request.method == "GET":
        return "Essa é a pagina da criação de urls curtas"

    links_pertencem_usuario = db.session.query(func.count(Link.id)).filter(Link.user_id == session["user_id"]).scalar()

    if links_pertencem_usuario >= limite_plano_gratis:
        return ("Limite de urls atingido", 403)

    url = request.json.get("original_url")

    if not isinstance(url, str) or not url.strip():
        return("Url não indentificada ou envie uma url", 400)

    url = url.strip()

    if len(url) > current_app.config["LIMITE_TAMANHO_URL"]:
        return ("Tamanho de url não suportada", 400)
    
    url_partes = urlparse(url)

    if url_partes.scheme not in ("http", "https") or not url_partes.netloc:
        return ("Envie uma url valida contendo http ou https", 400)    

    encurtador = EncurtadorBase62()
    link_model = Link(original_url = url, user_id = session["user_id"])

    while True:
        codigo = encurtador.gerar_codigo_aleatorio(6)

        verificacão = db.session.query(Link).filter(Link.short_code == codigo).first()

        link_model.short_code = codigo

        if verificacão is None:
            break



    db.session.add(link_model)
    db.session.commit()

    return {
        "short_url": current_app.config["BASE_URL"] + link_model.short_code

    }