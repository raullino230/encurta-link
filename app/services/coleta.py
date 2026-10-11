import ipaddress
from urllib.parse import unquote, urlparse

from flask import current_app
from user_agents import parse as interpretar_user_agent

from app.services.protecao_ip import hash_visitante


def _ip_valido(texto):
    try:
        return str(ipaddress.ip_address((texto or "").strip()))
    except ValueError:
        return None


def _ip_visitante(request):
    # Na Vercel, x-forwarded-for é preenchido pela própria plataforma.
    # Fora dela esse header pode ser forjado, por isso o IP é validado.
    candidatos = [
        request.headers.get("x-forwarded-for", "").split(",")[0],
        request.headers.get("x-real-ip", ""),
        request.remote_addr,
    ]
    for candidato in candidatos:
        ip = _ip_valido(candidato)
        if ip:
            return ip
    return None


def _pais(request):
    pais = request.headers.get("x-vercel-ip-country", "").strip().upper()
    if len(pais) == 2 and pais.isalpha():
        return pais
    return None


def _cidade(request):
    cidade = unquote(request.headers.get("x-vercel-ip-city", "")).strip()
    return cidade[:100] or None


def _origem(request):
    referrer = request.referrer
    if not referrer:
        return None

    try:
        dominio = urlparse(referrer).hostname
    except ValueError:
        return None

    if not dominio:
        return None

    dominio = dominio.lower()

    proprios = {request.host.rsplit(":", 1)[0].lower()}
    base_url = current_app.config.get("BASE_URL")
    if base_url:
        host_base = urlparse(base_url).hostname
        if host_base:
            proprios.add(host_base.lower())

    if dominio in proprios:
        return None

    return dominio[:255]


def _aparelho(request):
    texto = request.user_agent.string
    if not texto:
        return None, None

    try:
        ua = interpretar_user_agent(texto)

        if ua.is_bot:
            dispositivo = "bot"
        elif ua.is_mobile:
            dispositivo = "celular"
        elif ua.is_tablet:
            dispositivo = "tablet"
        elif ua.is_pc:
            dispositivo = "computador"
        else:
            dispositivo = None

        navegador = (ua.browser.family or "")[:50] or None
        return dispositivo, navegador
    except Exception:
        return None, None


def _seguro(funcao, request, padrao=None):
    try:
        return funcao(request)
    except Exception:
        return padrao


def extrair_dados_clique(request):
    ip = _seguro(_ip_visitante, request)
    dispositivo, navegador = _seguro(_aparelho, request, padrao=(None, None))

    try:
        visitante = hash_visitante(ip)
    except Exception:
        visitante = None

    dados = {
        "pais": _seguro(_pais, request),
        "cidade": _seguro(_cidade, request),
        "dispositivo": dispositivo,
        "navegador": navegador,
        "origem": _seguro(_origem, request),
        "visitante_hash": visitante,
    }
    return dados, ip