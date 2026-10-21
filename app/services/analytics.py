from datetime import datetime, timedelta, timezone
from app.planos import historico_dias
from app.models import Link, Click
from app import db
from sqlalchemy import func
import math

PERIODOS = (7, 30, 90, 365)
FUSO_BRASIL = timezone(timedelta(hours = -3))
ROTULO_DESCONHECIDO = "Desconhecido"
ROTULO_DIRETO = "Direto"
COLUNAS_RANKING = ("pais", "cidade", "dispositivo", "navegador", "origem")
DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

def periodos_disponiveis(user):
    limite_dias = historico_dias(user)

    permitidos = []
    for periodo in PERIODOS:
        if periodo <= limite_dias:
            permitidos.append(periodo)

    return permitidos

def normalizar_periodo(valor, user):
    try:
        numero = int(valor)
    except (ValueError, TypeError):
        return 7

    periodos_liberados = periodos_disponiveis(user)

    if numero not in periodos_liberados:
        return 7
    
    return numero


def inicio_do_periodo(dias):
    hoje = datetime.now(FUSO_BRASIL).date()
    meia_noite = datetime.combine(hoje, datetime.min.time(), tzinfo = FUSO_BRASIL)
    inicio = meia_noite - timedelta(days = dias - 1)
    dt_utc = inicio.astimezone(timezone.utc)

    return dt_utc

def _cliques_do_periodo(user_id, dias, link_id = None):
    consulta = db.session.query(Click).join(Link, Link.id == Click.link_id)

    consulta = consulta.filter(Link.user_id == user_id)

    consulta = consulta.filter(Click.clicked_at >= inicio_do_periodo(dias))

    if link_id is not None:
        consulta = consulta.filter(Click.link_id == link_id)

    return consulta

def _para_horario_brasilia(momento):
    if momento.tzinfo is None:
       colocar_fuso = momento.replace(tzinfo = timezone.utc)
       momento = colocar_fuso
    fuso = momento.astimezone(FUSO_BRASIL)

    return fuso

def resumo(user_id, dias, link_id = None):
    consulta = _cliques_do_periodo(user_id, dias, link_id)    
    total_cliques = consulta.with_entities(func.count(Click.id)).scalar()
    visitantes_unicos = consulta.with_entities(func.count(Click.visitante_hash.distinct())).scalar()
    links_ativos = db.session.query(func.count(Link.id)).filter(Link.user_id == user_id).filter(Link.is_active.is_(True)).scalar()

    media_por_dia = round(total_cliques / dias, 1)

    return {
        "total_cliques": total_cliques,
        "visitantes_unicos": visitantes_unicos,
        "links_ativos": links_ativos,
        "media_dia": media_por_dia,
    }

def serie_cliques(user_id, dias, link_id = None):
    consulta = _cliques_do_periodo(user_id, dias, link_id)
    datas_dos_cliques = consulta.with_entities(Click.clicked_at).all()

    dta_brasilia = []
    for (data,) in datas_dos_cliques:
        dta_convertida = _para_horario_brasilia(data)
        dta_brasilia.append(dta_convertida)

    inicio = inicio_do_periodo(dias)
    inicio_brasilia = _para_horario_brasilia(inicio).date()

    if dias == 365:
        fim = inicio_brasilia + timedelta(days = dias - 1)
        ano_inicio = inicio_brasilia.year
        mes_inicio = inicio_brasilia.month
        ano_fim = fim.year
        mes_fim = fim.month

        chaves = []
        while (ano_inicio, mes_inicio) <= (ano_fim, mes_fim):
            chaves.append((ano_inicio, mes_inicio))
            mes_inicio += 1
            if mes_inicio > 12:
                mes_inicio = 1
                ano_inicio += 1

        contador_mes = {}
        for periodo in chaves:
            contador_mes[periodo] = 0

        for clique in dta_brasilia:
            chave = (clique.year, clique.month)
            contador_mes[chave] += 1

        resultado = []
        for (ano, mes) in chaves:
            rotulo = f"{MESES[mes - 1]}/{ano}"
            total = contador_mes[(ano, mes)]
            resultado.append((rotulo, total))

        return resultado
    
    if dias <= 30:
        tamanho = 1
    elif dias == 90:
        tamanho = 7
    

    total_de_grupos = math.ceil(dias / tamanho)

    contadores = []
    for numero in range(total_de_grupos):
        contadores.append(0)
    
    for clique in dta_brasilia:
        diferenca = (clique.date() - inicio_brasilia).days
        bloco = diferenca // tamanho
        contadores[bloco] += 1

    rotulos = []
    for posicao in range(total_de_grupos):
        dta_comeco = inicio_brasilia + timedelta(days=posicao * tamanho)
        if dias == 7:
            rotulos.append(DIAS_SEMANA[dta_comeco.weekday()])
        elif dias in (30, 90):
            rotulos.append(dta_comeco.strftime("%d/%m"))

    total_rotulado = []
    for posicao in range(total_de_grupos):
        rotulo = rotulos[posicao]
        contador = contadores[posicao]
        total_rotulado.append((rotulo, contador))    
    return total_rotulado

def cliques_por_hora(user_id, dias, link_id = None):
    consulta = _cliques_do_periodo(user_id, dias, link_id)
    datas_dos_cliques = consulta.with_entities(Click.clicked_at).all()

    dta_brasilia = []
    for (data,) in datas_dos_cliques:
        dta_convertida = _para_horario_brasilia(data)
        dta_brasilia.append(dta_convertida)

    contadores_horas = []
    for hora in range(24):
        contadores_horas.append(0)

    for clique in dta_brasilia:
        contadores_horas[clique.hour] += 1

    return contadores_horas

def ranking(coluna, user_id, dias, link_id = None, limite = 10):
    if coluna not in COLUNAS_RANKING:
        raise ValueError("Coluna não permitida")

    consulta = _cliques_do_periodo(user_id, dias, link_id)

    nome = coluna
    coluna_do_click = getattr(Click, nome)

    linhas = (
        consulta
        .with_entities(coluna_do_click, func.count(Click.id))
        .group_by(coluna_do_click)
        .order_by(func.count(Click.id).desc())
        .all()
    )

    soma = 0
    for (valor, total) in linhas:
        soma += total

    resultado = []
    for (valor, total) in linhas:
        if valor is None:
            if coluna == "origem":
                valor = ROTULO_DIRETO
            else:
                valor = ROTULO_DESCONHECIDO

        percentual = round(total / soma * 100)
        resultado.append((valor, total, percentual))

    return resultado[:limite]

def links_mais_clicados(user_id, dias, link_id = None, limite = 5):
    consulta = _cliques_do_periodo(user_id, dias, link_id)

    linhas = (
        consulta
        .with_entities(Link.short_code, func.count(Click.id))
        .group_by(Link.short_code)
        .order_by(func.count(Click.id).desc())
        .all()
    )

    resultado = []
    for (codigo, total) in linhas:
        resultado.append((codigo, total))

    return resultado[:limite]