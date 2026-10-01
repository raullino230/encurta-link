from flask import Blueprint, session, redirect
from fasthtml.common import to_xml
from app.frontend.componentes_landing import LandingPage, Layout

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")  # ajusta se sua rota do menu tiver outro caminho

    rendenização_front = to_xml(Layout(LandingPage()))
    return rendenização_front