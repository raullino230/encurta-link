from flask import Blueprint, current_app, url_for, session, redirect
from app import oauth, limiter
from app.models import db, User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
@limiter.limit(
    "10/minute"
)
def login():
    redirect_uri = (
        current_app.config["BASE_URL"].rstrip("/")
        + url_for("auth.callback_google")
    )
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route("/callback/google")
def callback_google():
    token = oauth.google.authorize_access_token()
    dados_usuario = token["userinfo"]

    user = db.session.query(User).filter(User.google_id == dados_usuario["sub"]).first()

    if user is None:
        create_user = User(email = dados_usuario["email"], name = dados_usuario["name"], google_id = dados_usuario["sub"])

        db.session.add(create_user)
        db.session.commit()
        user = create_user

    session.clear()
    session.permanent = True
    session["user_id"] = user.id

    return redirect(url_for("dashboard.ver_dashboard"))

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")
