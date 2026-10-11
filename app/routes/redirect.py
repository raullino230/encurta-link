from flask import Blueprint, abort, current_app, redirect, request

from app.models import Click, Link, RegistroAcesso, db
from app.services.coleta import extrair_dados_clique
from app.services.protecao_ip import cifrar_ip

redirect_bp = Blueprint("redirect", __name__)


@redirect_bp.route("/<short_code>")
def go_to_original(short_code):
    link_model = (
        db.session.query(Link)
        .filter(Link.short_code == short_code, Link.is_active == True)
        .first()
    )

    if link_model is None:
        abort(404)

    # Guardados antes de qualquer commit/rollback, que "expiram" o objeto
    destino = link_model.original_url
    link_id = link_model.id

    try:
        dados, ip = extrair_dados_clique(request)

        db.session.add(
            Click(
                link_id=link_id,
                user_agent=(request.user_agent.string or "")[:255],
                **dados,
            )
        )

        ip_cifrado = cifrar_ip(ip)
        if ip_cifrado:
            db.session.add(RegistroAcesso(link_id=link_id, ip_cifrado=ip_cifrado))

        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Falha ao registrar clique")

    return redirect(destino)