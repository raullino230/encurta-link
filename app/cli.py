from datetime import timedelta

import click

from app import db
from app.models import User, utcnow


def registrar_comandos(app):
    @app.cli.command("definir-plano")
    @click.argument("email")
    @click.argument("plano", type=click.Choice(["gratuito", "pro"]))
    @click.argument("dias", default=30, type=click.IntRange(min=1))
    def definir_plano(email, plano, dias):
        """Define o plano de um usuário. Ex: flask definir-plano a@b.com pro 30"""
        user = User.query.filter_by(email=email).first()

        if user is None:
            raise click.ClickException(f"Usuário {email} não encontrado.")

        if plano == "pro":
            user.plano = "pro"
            user.data_renovacao = utcnow() + timedelta(days=dias)
            db.session.commit()
            click.echo(f"{email} agora é Pro até {user.data_renovacao:%d/%m/%Y}.")
        else:
            user.plano = "gratuito"
            user.data_renovacao = None
            db.session.commit()
            click.echo(f"{email} voltou para o plano gratuito.")