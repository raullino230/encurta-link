import pytest

from app import create_app, db
from app.models import User


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SECRET_KEY": "chave-apenas-para-testes",
        "BASE_URL": "http://localhost:5000/",
        "GOOGLE_CLIENT_ID": "cliente-de-teste",
        "GOOGLE_CLIENT_SECRET": "segredo-de-teste",
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_STORAGE_URI": "memory://",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def user_teste(app):
    with app.app_context():
        user = User(
            google_id="google-id-de-teste",
            name="Usuário de teste",
            email="teste@example.com",
        )
        db.session.add(user)
        db.session.commit()
        return user.id
