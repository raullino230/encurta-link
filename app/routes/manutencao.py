import hmac

from flask import Blueprint, current_app, jsonify, request

from app import limiter
from app.services.retencao import executar_retencao

manutencao_bp = Blueprint("manutencao", __name__, url_prefix="/manutencao")


@manutencao_bp.route("/retencao", methods=["GET"])
@limiter.exempt
def rodar_retencao():
    segredo = current_app.config.get("CRON_SECRET")
    recebido = request.headers.get("Authorization", "")

    if not segredo or not hmac.compare_digest(recebido, f"Bearer {segredo}"):
        return jsonify({"erro": "não autorizado"}), 401

    resultado = executar_retencao()
    return jsonify(resultado), 200