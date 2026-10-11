from datetime import timedelta

import click

from app import db
from app.models import Click, RegistroAcesso, User, utcnow
from app.services.protecao_ip import cifrar_ip, hash_visitante, parece_cifrado


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

    @app.cli.command("proteger-ips")
    @click.option("--lote", default=500, type=click.IntRange(min=1))
    def proteger_ips(lote):
        """Move os IPs em texto puro do Click para RegistroAcesso, cifrados."""
        if cifrar_ip("127.0.0.1") is None:
            raise click.ClickException("IP_CRIPTO_CHAVE ausente ou inválida.")
        if hash_visitante("127.0.0.1") is None:
            raise click.ClickException("HASH_SEGREDO ausente.")

        movidos = 0

        while True:
            cliques = (
                Click.query.filter(Click.ip_address.is_not(None))
                .order_by(Click.id)
                .limit(lote)
                .all()
            )
            if not cliques:
                break

            for clique in cliques:
                ip = clique.ip_address
                ja_cifrado = parece_cifrado(ip)

                ip_cifrado = ip if ja_cifrado else cifrar_ip(ip)

                if ip_cifrado and clique.link_id is not None:
                    db.session.add(
                        RegistroAcesso(
                            link_id=clique.link_id,
                            acessado_em=clique.clicked_at,
                            ip_cifrado=ip_cifrado,
                        )
                    )

                if clique.visitante_hash is None and not ja_cifrado:
                    clique.visitante_hash = hash_visitante(ip)

                clique.ip_address = None
                movidos += 1

            db.session.commit()

        click.echo(f"{movidos} cliques protegidos.")