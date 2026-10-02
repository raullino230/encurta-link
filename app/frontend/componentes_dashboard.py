from fasthtml.common import *
from flask_wtf.csrf import generate_csrf


# =====================================================================
# SIDEBAR — barra lateral reaproveitada nas 3 páginas internas.
# Recebe qual item deve aparecer "ativo" (destacado em verde).
# =====================================================================
def Sidebar(pagina_ativa: str):
    """
    pagina_ativa: "links" | "analytics" | "configuracoes"
    Usado pra aplicar a classe "ativo" no item certo do menu.
    """

    # Lista de itens do menu: (texto, rota, chave de identificação, ícone)
    # A chave é comparada com `pagina_ativa` pra saber qual destacar.
    itens_menu = [
        ("Meus links", "/dashboard", "links", "🔗"),
        ("Analytics", "/dashboard/analytics", "analytics", "📊"),
    ]

    def ItemMenu(texto, rota, chave, icone):
        # Se a chave bate com a página atual, adiciona "ativo" na classe.
        classe = "menu-item ativo" if chave == pagina_ativa else "menu-item"
        return A(Span(icone, cls="menu-icon"), texto, href=rota, cls=classe)

    return Aside(
        Div("🔗 encurta-link", cls="sidebar-logo"),

        A("+ Criar novo", href="/dashboard", cls="btn-criar-novo"),

        Nav(
            *[ItemMenu(*item) for item in itens_menu],
            cls="menu-principal"
        ),

        # Configurações fica separada por uma linha, no rodapé da sidebar
        Div(
            A(
                Span("⚙️", cls="menu-icon"),
                "Configurações",
                href="/dashboard/configuracoes",
                cls="menu-item ativo" if pagina_ativa == "configuracoes" else "menu-item"
            ),
            cls="sidebar-rodape"
        ),

        cls="sidebar"
    )


# =====================================================================
# SHELL — estrutura comum das páginas internas: sidebar + conteúdo.
# Cada página (MeusLinksPage, AnalyticsPage, ConfiguracoesPage) só
# precisa montar o que vai dentro de `conteudo`.
# =====================================================================
def DashboardShell(pagina_ativa: str, *conteudo):
    return Div(
        
        Button(
            "☰",
            id = "btn-menu-mobile",
            cls = "btn-menu-mobile",
            type = "button",
        ),

        Div(id = "overlay-sidebar", cls = "overlay-sidebar"),

        Sidebar(pagina_ativa),
        Main(*conteudo, cls="dashboard-main"),
        cls="dashboard-layout"
    )


# =====================================================================
# MEUS LINKS — lista de links do usuário logado.
# `links` é uma lista de objetos/dicts vindos do banco, cada um
# esperado com: short_code, original_url, total_cliques, created_at, is_active
# =====================================================================
def LinhaLink(link):
    status_texto = "ativo" if link["is_active"] else "inativo"
    status_classe = "status-badge ativo" if link["is_active"] else "status-badge inativo"
    # Link inativo fica com opacidade reduzida (decisão de design já combinada)
    linha_classe = "link-row" if link["is_active"] else "link-row inativo"

    return Div(
        Div(
            Span(f"curta.link/{link['short_code']}", cls="link-code"),
            Span(link["original_url"], cls="link-url"),
            cls="link-info"
        ),
        Div(
            Span(f"📊 {link['total_cliques']} cliques", cls="link-meta"),
            Span(link["created_at"], cls="link-meta"),
            Span(status_texto, cls=status_classe),
            cls="link-stats"
        ),
        cls=linha_classe
    )


def FormularioCriarLink():
    """Form de criação de link, exibido no topo de Meus Links."""
    return Div(
        Form(
            Input(
                type="url",
                name="original_url",
                placeholder="Cole a URL que você quer encurtar...",
                required=True
            ),
            Button("Criar link", type="submit"),
            id="form-criar-link",
            cls="shorten-form"
        ),
        Div(id="resultado-criar-link", cls="resultado-encurtar"),
        cls="card-criar-link"
    )


def MeusLinksPage(links: list, total_links: int, total_cliques: int):
    """
    `links`: lista de links do usuário (já formatada, ver LinhaLink acima)
    `total_links` / `total_cliques`: números pro resumo no topo
    """
    return DashboardShell(
        "links",

        Div(
            H2("Meus links"),
            Div(
                Span(f"{total_links} links"),
                Span(f"{total_cliques} cliques"),
                cls="resumo-topo"
            ),
            cls="pagina-header"
        ),

        FormularioCriarLink(),

        Div(
            *[LinhaLink(link) for link in links],
            cls="lista-links"
        ) if links else P("Você ainda não criou nenhum link.", cls="estado-vazio")
    )


# =====================================================================
# ANALYTICS — resumo + gráfico de barras + top links.
# `cliques_por_dia`: lista de tuplas (dia_abreviado, valor_percentual_altura)
# `top_links`: lista de tuplas (short_code, total_cliques)
# =====================================================================
def CardResumo(label, valor):
    return Div(
        Div(label, cls="card-label"),
        Div(str(valor), cls="card-valor"),
        cls="card-resumo"
    )


def BarraGrafico(dia, altura_percentual, destaque=False):
    # `altura_percentual` de 0 a 100 — controla a altura da barra via style inline
    cor = "barra destaque" if destaque else "barra"
    return Div(
        Div(cls=cor, style=f"height: {altura_percentual}%;"),
        Span(dia, cls="barra-label"),
        cls="barra-coluna"
    )


def AnalyticsPage(cliques_7_dias, links_ativos, media_dia, cliques_por_dia, top_links):
    return DashboardShell(
        "analytics",

        H2("Analytics"),

        Div(
            CardResumo("cliques (7 dias)", cliques_7_dias),
            CardResumo("links ativos", links_ativos),
            CardResumo("média/dia", media_dia),
            cls="grid-resumo"
        ),

        Div(
            H3("Cliques por dia"),
            Div(
                *[
                    BarraGrafico(dia, altura, destaque=(i == len(cliques_por_dia) - 1))
                    for i, (dia, altura) in enumerate(cliques_por_dia)
                ],
                cls="grafico-barras"
            ),
            cls="card-grafico"
        ),

        Div(
            H3("Links mais clicados"),
            Div(
                *[
                    Div(
                        Span(f"curta.link/{codigo}", cls="link-code"),
                        Span(f"{cliques} cliques", cls="link-meta"),
                        cls="ranking-item"
                    )
                    for codigo, cliques in top_links
                ],
                cls="ranking-lista"
            ),
            cls="card-ranking"
        )
    )


# =====================================================================
# CONFIGURAÇÕES — conta, plano, sair.
# `usuario`: dict com name, email
# `links_usados` / `limite_plano`: números pra barra de progresso
# =====================================================================
def ConfiguracoesPage(usuario, links_usados, limite_plano, plano_nome="Grátis"):
    iniciais = "".join([parte[0] for parte in usuario["name"].split()[:2]]).upper()
    percentual_uso = min(100, int((links_usados / limite_plano) * 100))

    return DashboardShell(
        "configuracoes",

        H2("Configurações"),

        Div(
            Div(iniciais, cls="avatar"),
            Div(
                Div(usuario["name"], cls="conta-nome"),
                Div(usuario["email"], cls="conta-email"),
                cls="conta-info"
            ),
            cls="card-conta"
        ),

        Div(
            Div(
                Span(f"Plano {plano_nome}", cls="plano-nome"),
                Span("ativo", cls="status-badge ativo"),
                cls="plano-header"
            ),
            P(f"{links_usados} de {limite_plano} links usados", cls="plano-uso"),
            Div(
                Div(cls="barra-progresso-preenchida", style=f"width: {percentual_uso}%;"),
                cls="barra-progresso"
            ),
            Button("Fazer upgrade", cls="btn-upgrade"),
            cls="card-plano"
        ),

        Form(
            Input(type = "hidden", name = "csrf_token", value = generate_csrf()),
            Button("Sair da conta", type="submit", cls="btn-sair"),
            action="/logout",
            method="post",
        )
    )