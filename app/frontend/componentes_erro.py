from fasthtml.common import Div, H1, P, A


def ErroPage(codigo, titulo, mensagem, acao_texto=None, acao_link=None):
    botoes = []

    if acao_texto and acao_link:
        botoes.append(A(acao_texto, href=acao_link, cls="erro-btn erro-btn-primario"))

    botoes.append(A("Voltar ao início", href="/", cls="erro-btn erro-btn-secundario"))

    return Div(
        Div(str(codigo), cls="erro-codigo"),
        H1(titulo, cls="erro-titulo"),
        P(mensagem, cls="erro-mensagem"),
        Div(*botoes, cls="erro-acoes"),
        cls="erro-container",
    )