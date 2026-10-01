from fasthtml.common import *
from flask_wtf.csrf import generate_csrf


def Navbar():
    return Header(
        Div(
            A("encurta-link", href="/", cls="logo"),

            Nav(
                A("Recursos", href="#recursos"),
                A("Preços", href="#precos"),
                cls="nav-links"
            ),

            A(
                "Entrar",
                href="/login",
                cls="btn-login"
            ),

            cls="nav-container"
        ),
        cls="navbar"
    )


def Layout(conteudo):
    return Html(
        Head(
            Title("encurta-link"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Meta(name="csrf-token", content=generate_csrf()),
            Link(rel="stylesheet", href="/static/style.css"),
        ),
        Body(
            Canvas(id="dots-canvas"),
            conteudo,
            Script(src="/static/dots.js"),
            Script(src="/static/shorten.js"),
            Script(src="/static/criar-link.js"),   
        ),
    )

def Hero():
    return Section(
        Div(
            Span(
                "Feito pra quem compartilha muitos links",
                cls="badge"
            ),

            H1(
                "Links longos?",
                Br(),
                Span("Encurte. Compartilhe. ", cls="highlight"),
                "Pronto."
            ),

            P(
                "Transforme links enormes em URLs curtas, bonitas e fáceis de compartilhar.",
                cls="hero-subtitle"
            ),

            P(
                "Grátis até 10 links.",
                cls="free-text"
            ),

            Form(
                Input(
                    type="url",
                    name="original_url",
                    placeholder="Cole seu link aqui...",
                    required=True
                ),
                Button("Encurtar", type="submit"),
                action="/links",
                method="post",
                id="form-encurtar",          # <- adicionar
                cls="shorten-form"
            ),

            Div(cls="resultado-encurtar"),   # <- adicionar logo depois do Form

            cls="hero-content"
        ),
        cls="hero"
    )


def Recursos():
    recursos = [
        (
            "✂️",
            "Links curtos",
            "Transforme URLs enormes em links simples e fáceis de compartilhar."
        ),
        (
            "📊",
            "Analytics",
            "Acompanhe os acessos aos seus links de forma simples e rápida."
        ),
        (
            "🚀",
            "Pra quem é",
            "Ideal para criadores, estudantes, empresas e qualquer pessoa que compartilha links."
        )
    ]

    return Section(
        H2("Recursos"),

        Div(
            *[
                Article(
                    Div(icone, cls="resource-icon"),
                    H3(titulo),
                    P(descricao),
                    cls="resource-card"
                )
                for icone, titulo, descricao in recursos
            ],
            cls="resources-grid"
        ),

        id="recursos",
        cls="resources"
    )


def Precos():
    return Section(
        H2("Preços"),

        Div(
            Article(
                H3("Grátis"),
                P("Para começar a encurtar seus links."),

                Div(
                    Strong("R$0"),
                    Span("/mês"),
                    cls="price"
                ),

                Ul(
                    Li("Até 10 links"),
                    Li("Links curtos"),
                    Li("Compartilhamento fácil")
                ),

                Button("Começar grátis"),

                cls="price-card"
            ),

            Article(
                Span("Popular", cls="popular-badge"),

                H3("Pro"),
                P("Para quem precisa de mais recursos."),

                Div(
                    Strong("R$5"),
                    Span("/mês"),
                    cls="price"
                ),

                Ul(
                    Li("Até 400 links"),
                    Li("Analytics"),
                    Li("Mais recursos")
                ),

                Button("Assinar Pro"),

                cls="price-card pro-card"
            ),

            cls="pricing-grid"
        ),

        id="precos",
        cls="pricing"
    )


def RodapéPagina():
    """Rodapé simples: 'curta.link — feito com Flask e FastHTML'."""

    return Footer(
        P(
            "encurta-link"
        ),
        cls="footer"
    )


def LandingPage():
    """Monta a página inteira."""

    return Div(
        Navbar(),
        Hero(),
        Recursos(),
        Precos(),
        RodapéPagina(),

        cls="page"
    )