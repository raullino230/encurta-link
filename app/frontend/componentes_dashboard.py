from fasthtml.common import *
from app.frontend.constantes import NOME_MARCA, DOMINIO_EXIBICAO
from flask_wtf.csrf import generate_csrf
from urllib.parse import quote


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
        Div(f"🔗 {NOME_MARCA}", cls="sidebar-logo"),

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
            Span(f"{DOMINIO_EXIBICAO}/{link['short_code']}", cls="link-code"),
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
# ANALYTICS — resumo, gráficos, rankings e seletores.
# Gratuito: básico (7 dias) + blocos avançados bloqueados, só com texto fixo.
# Pro: períodos, filtro por link, visitantes únicos, rankings e horários.
# =====================================================================
PERIODOS_EXIBIDOS = (7, 30, 90, 365)

# Ordem e títulos dos rankings (as chaves são as colunas de COLUNAS_RANKING)
TITULOS_RANKING = {
    "pais": "Países",
    "cidade": "Cidades",
    "dispositivo": "Dispositivos",
    "navegador": "Navegadores",
    "origem": "Origem dos cliques",
}


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


def SeletorPeriodo(periodo_atual, liberados, link_atual):
    botoes = []
    for dias in PERIODOS_EXIBIDOS:
        rotulo = f"{dias} dias"
        if dias in liberados:
            url = f"/dashboard/analytics?periodo={dias}"
            if link_atual:
                url += f"&link={quote(link_atual)}"
            classe = "periodo-opcao ativo" if dias == periodo_atual else "periodo-opcao"
            botoes.append(A(rotulo, href=url, cls=classe))
        else:
            # não liberado: cadeado e caminho para o upgrade
            botoes.append(
                A(f"🔒 {rotulo}", href="/dashboard/configuracoes", cls="periodo-opcao travado")
            )
    return Div(*botoes, cls="seletor-periodo")


def SeletorLink(links, link_atual):
    opcoes = [Option("Todos os links", value="", selected=(link_atual is None))]
    for codigo in links:
        opcoes.append(Option(codigo, value=codigo, selected=(codigo == link_atual)))
    # O JavaScript de static/analytics.js recarrega a página ao escolher
    return Select(*opcoes, id="seletor-link", cls="seletor-link")


def GraficoSerie(serie):
    maior = max((total for _, total in serie), default=0)
    # Com 30 ou mais pontos, mostra o rótulo de 1 a cada 5
    passo = 5 if len(serie) >= 30 else 1
    ultimo = len(serie) - 1

    barras = []
    for posicao, (rotulo, total) in enumerate(serie):
        altura = int(total / maior * 100) if maior else 0
        texto = rotulo if posicao % passo == 0 else ""
        barras.append(BarraGrafico(texto, altura, destaque=(posicao == ultimo)))

    classe = "grafico-barras compacto" if len(serie) >= 30 else "grafico-barras"
    return Div(*barras, cls=classe)


def GraficoHoras(horas):
    maior = max(horas, default=0)

    barras = []
    for hora, total in enumerate(horas):
        altura = int(total / maior * 100) if maior else 0
        rotulo = f"{hora}h" if hora in (0, 6, 12, 18) else ""
        barras.append(BarraGrafico(rotulo, altura))

    return Div(
        H3("Horários"),
        Div(*barras, cls="grafico-barras grafico-horas compacto"),
        cls="card-grafico"
    )


def LinhaRanking(rotulo, total, percentual):
    return Div(
        Div(
            Span(rotulo, cls="link-code"),
            Span(str(total), cls="link-meta"),
            cls="ranking-item"
        ),
        Div(
            Div(cls="ranking-barra", style=f"width: {percentual}%;"),
            cls="ranking-trilho"
        ),
        cls="ranking-linha"
    )


def BlocoRanking(titulo, linhas):
    if linhas:
        corpo = [LinhaRanking(rotulo, total, perc) for rotulo, total, perc in linhas]
    else:
        corpo = [P("Sem dados no período.", cls="estado-vazio")]
    return Div(H3(titulo), *corpo, cls="card-ranking bloco-ranking")


def BlocoBloqueado(titulo):
    # Linhas de exemplo escritas à mão. NUNCA use dados reais do usuário aqui.
    exemplos = [("Exemplo A", 120, 60), ("Exemplo B", 50, 25), ("Exemplo C", 30, 15)]
    return Div(
        H3(titulo),
        Div(
            *[LinhaRanking(rotulo, total, perc) for rotulo, total, perc in exemplos],
            cls="exemplo-borrado"
        ),
        Div(
            P("Disponível no Pro"),
            A("Fazer upgrade", href="/dashboard/configuracoes", cls="btn-upgrade"),
            cls="bloqueado-aviso"
        ),
        cls="card-ranking bloco-bloqueado"
    )


def AnalyticsPage(periodo, periodos_liberados, resumo, serie, top_links, is_pro,
                  link_atual=None, links_do_usuario=None, horas=None, rankings=None):
    # 1. Cabeçalho: título + seletor de período (e de link, só no Pro)
    seletores = [SeletorPeriodo(periodo, periodos_liberados, link_atual)]
    if is_pro:
        seletores.append(SeletorLink(links_do_usuario or [], link_atual))

    cabecalho = Div(
        H2("Analytics"),
        Div(*seletores, cls="seletores"),
        cls="analytics-cabecalho"
    )

    # 2. Cartões de resumo (Pro ganha "visitantes únicos")
    cartoes = [
        CardResumo(f"cliques ({periodo} dias)", resumo["total_cliques"]),
        CardResumo("links ativos", resumo["links_ativos"]),
        CardResumo("média/dia", resumo["media_dia"]),
    ]
    if is_pro:
        cartoes.append(CardResumo("visitantes únicos", resumo["visitantes_unicos"]))
    classe_resumo = "grid-resumo com-quatro" if is_pro else "grid-resumo"

    # 3. Gráfico de cliques: o título muda com o período
    unidade = {90: "semana", 365: "mês"}.get(periodo, "dia")
    grafico = Div(
        H3(f"Cliques por {unidade}"),
        GraficoSerie(serie),
        cls="card-grafico"
    )

    # 4. Links mais clicados
    if top_links:
        itens_top = [
            Div(
                Span(f"{DOMINIO_EXIBICAO}/{codigo}", cls="link-code"),
                Span(f"{cliques} cliques", cls="link-meta"),
                cls="ranking-item"
            )
            for codigo, cliques in top_links
        ]
    else:
        itens_top = [P("Sem dados no período.", cls="estado-vazio")]

    bloco_top = Div(
        H3("Links mais clicados"),
        Div(*itens_top, cls="ranking-lista"),
        cls="card-ranking"
    )

    # 5 e 6. Pro: dados reais. Gratuito: só blocos bloqueados com texto fixo.
    if is_pro:
        bloco_horas = GraficoHoras(horas)
        blocos_ranking = [
            BlocoRanking(titulo, (rankings or {}).get(coluna, []))
            for coluna, titulo in TITULOS_RANKING.items()
        ]
        extras = [Script(src="/static/analytics.js")]
    else:
        bloco_horas = BlocoBloqueado("Horários")
        blocos_ranking = [BlocoBloqueado(titulo) for titulo in TITULOS_RANKING.values()]
        extras = []

    return DashboardShell(
        "analytics",

        cabecalho,
        Div(*cartoes, cls=classe_resumo),
        grafico,
        bloco_top,
        bloco_horas,
        # 7. Grade de 2 colunas no desktop e 1 no celular (ver CSS)
        Div(*blocos_ranking, cls="grid-rankings"),
        *extras
    )


# =====================================================================
# CONFIGURAÇÕES — conta, plano, sair.
# `usuario`: dict com name, email
# `links_usados` / `limite_plano`: números pra barra de progresso
# =====================================================================
def ConfiguracoesPage(usuario, links_usados, limite_plano, plano_nome="Gratuito", is_pro=False):
    iniciais = "".join([parte[0] for parte in usuario["name"].split()[:2]]).upper()
    percentual_uso = min(100, int((links_usados / limite_plano) * 100))

    # Pro não vê o botão de upgrade
    botao_upgrade = [] if is_pro else [Button("Fazer upgrade", cls="btn-upgrade")]

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
            *botao_upgrade,
            cls="card-plano"
        ),

        Form(
            Input(type="hidden", name="csrf_token", value=generate_csrf()),
            Button("Sair da conta", type="submit", cls="btn-sair"),
            action="/logout",
            method="post",
        )
    )