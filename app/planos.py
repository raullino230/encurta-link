PLANOS = {
    "gratuito": {
        "nome": "Gratuito",
        "limite_links": 15,
        "historico_dias": 7
    },

    "pro": {
        "nome": "Pro",
        "limite_links": 500,
        "historico_dias": 365
    },
}

def obter_plano(user):
    if user.is_pro == True:
        return "pro"
    else:
        return "gratuito"

def regras_do_plano(user):
    return PLANOS[obter_plano(user)]

def limite_links(user):
    return regras_do_plano(user)["limite_links"]

def historico_dias(user):
    return regras_do_plano(user)["historico_dias"]