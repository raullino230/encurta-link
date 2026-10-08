from flask import Blueprint, redirect, request, abort
from app.models import Link, db, Click

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

    clique = Click(
        link_id=link_model.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
    )

    db.session.add(clique)
    db.session.commit()

    return redirect(link_model.original_url)