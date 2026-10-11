from flask import current_app
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import hmac
import ipaddress

def _fernet():
    chave = current_app.config.get("IP_CRIPTO_CHAVE")

    if not chave:
        return None

    try:
        return Fernet(chave)
    except (ValueError, TypeError):
        return None

def cifrar_ip(ip):
    f = _fernet()

    if not ip or f is None:
        return None

    try:
        return f.encrypt(ip.encode()).decode()
    except Exception:
        return None

def decifrar_ip(token):

    f = _fernet()
    if f is None or not token:
        return None

    try:
        texto_bytes = token.encode()
        decifrado = f.decrypt(texto_bytes)
        ip_texto = decifrado.decode()
        return ip_texto
    except InvalidToken:
        return None

def hash_visitante(ip):
    segredo = current_app.config.get("HASH_SEGREDO")

    if not ip or not segredo:
        return None

    try:
        endereco = ipaddress.ip_address(ip.strip())
    except ValueError:
        return None

    if endereco.version == 6:
        if endereco.ipv4_mapped:
            endereco = endereco.ipv4_mapped
        else:
            endereco = ipaddress.ip_network(f"{endereco}/64", strict = False)

    base = str(endereco)
    assinatura = hmac.new(segredo.encode(), base.encode(), hashlib.sha256)
    return assinatura.hexdigest()[:32]

def parece_cifrado(valor):
    if not isinstance(valor, str) or not valor:
        return False
    return valor.startswith("gAAAAA")
