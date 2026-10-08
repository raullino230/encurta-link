from flask import request, jsonify
from flask_wtf.csrf import CSRFError
from fasthtml.common import to_xml

from app import db
from app.frontend.constantes import ERROS
from app.frontend.componentes_erro import ErroPage
from app.frontend.componentes_landing import Layout

# Códigos que usam o texto padrão do ERROS, ignorando a description do Werkzeug
# (a do 429, por exemplo, vem como "10 per 1 minute")
CODIGOS_SEMPRE_PADRAO = {429, 500, 405}


def _quer_json():
    if request.path.startswith("/links"):
        return True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    melhor = request.accept_mimetypes.best_match(["text/html", "application/json"])
    return melhor == "application/json" and request.accept_mimetypes[melhor] > request.accept_mimetypes["text/html"]


def _mensagem_customizada(erro, codigo):
    """Usa a description passada via abort(codigo, description=...), se existir."""
    if codigo in CODIGOS_SEMPRE_PADRAO:
        return None
    descricao = getattr(erro, "description", None)
    classe = getattr(type(erro), "description", None)
    if descricao and descricao != classe:
        return descricao
    return None


def _responder(codigo, erro=None):
    dados = ERROS.get(codigo, ERROS[500])
    mensagem = (_mensagem_customizada(erro, codigo) if erro else None) or dados["mensagem"]

    if _quer_json():
        return jsonify({"erro": mensagem}), codigo

    pagina = ErroPage(
        codigo=codigo,
        titulo=dados["titulo"],
        mensagem=mensagem,
        acao_texto=dados["acao_texto"],
        acao_link=dados["acao_link"],
    )
    return to_xml(Layout(pagina)), codigo


def registrar_erros(app):
    for codigo in (401, 403, 404, 405, 413, 429):
        app.register_error_handler(codigo, lambda e, c=codigo: _responder(c, e))

    @app.errorhandler(CSRFError)
    def erro_csrf(e):
        return _responder(400)

    @app.errorhandler(500)
    def erro_interno(e):
        db.session.rollback()
        return _responder(500)