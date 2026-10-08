from app import db
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)
    short_code = db.Column(db.String(10), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime(timezone = True), default = utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Click(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    link_id = db.Column(db.Integer, db.ForeignKey("link.id"))
    clicked_at = db.Column(db.DateTime(timezone = True), default = utcnow, index = True)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    google_id = db.Column(db.String(255), unique = True)
    name = db.Column(db.Text)
    email = db.Column(db.Text, unique = True)
    created_at = db.Column(db.DateTime(timezone = True), default = utcnow)

class ClickResumo(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    link_id = db.Column(db.Integer ,db.ForeignKey("link.id"), nullable = False)
    data =  db.Column(db.Date, nullable = False)
    total_cliques = db.Column(db.Integer, nullable = False, default = 0)

    __table_args__ = (
        db.UniqueConstraint("link_id", "data", name="uq_click_resumo_link_data"),
    )