# Nome curto da marca, usado em logos e títulos (sidebar, navbar, rodapé).
NOME_MARCA = "encurta-link"

# Domínio completo, usado onde o link real é exibido (lista de links, ranking
# de analytics) — precisa bater com o BASE_URL de verdade, pra não confundir
# o usuário sobre pra onde o link aponta.
# Centralizado aqui pra não precisar caçar e trocar em vários arquivos quando
# o domínio mudar (ex: ao comprar um domínio próprio no futuro).
DOMINIO_EXIBICAO = "encurta-link-five.vercel.app"

ERROS = {
    400: {
        "titulo": "Sessão expirada",
        "mensagem": "Sua sessão expirou ou a requisição é inválida. Recarregue a página e tente novamente.",
        "acao_texto": "Recarregar",
        "acao_link": "/dashboard",
    },
    401: {
        "titulo": "Você precisa entrar",
        "mensagem": "Faça login com sua conta Google para acessar esta página.",
        "acao_texto": "Entrar com Google",
        "acao_link": "/login",
    },
    403: {
        "titulo": "Ação não permitida",
        "mensagem": "Você não tem permissão para fazer isso ou atingiu o limite do seu plano.",
        "acao_texto": "Ver meu plano",
        "acao_link": "/dashboard/configuracoes",
    },
    404: {
        "titulo": "Link não encontrado",
        "mensagem": "Esse link não existe, foi desativado ou o endereço está incorreto.",
        "acao_texto": None,
        "acao_link": None,
    },
    405: {
        "titulo": "Método não permitido",
        "mensagem": "Essa ação não é permitida neste endereço.",
        "acao_texto": None,
        "acao_link": None,
    },
    413: {
        "titulo": "Requisição grande demais",
        "mensagem": "O conteúdo enviado ultrapassa o tamanho permitido. Tente enviar algo menor.",
        "acao_texto": None,
        "acao_link": None,
    },
    429: {
        "titulo": "Calma, muitas tentativas",
        "mensagem": "Você fez muitas requisições em pouco tempo. Aguarde um minuto e tente de novo.",
        "acao_texto": None,
        "acao_link": None,
    },
    500: {
        "titulo": "Algo deu errado do nosso lado",
        "mensagem": "Tivemos um problema interno. Tente novamente em alguns instantes.",
        "acao_texto": None,
        "acao_link": None,
    },
}