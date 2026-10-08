(function () {
  const form = document.getElementById("form-criar-link");
  if (!form) return; // só existe na página Meus Links

  const resultado = document.getElementById("resultado-criar-link");
  const input = form.querySelector('input[name="original_url"]');
  const botao = form.querySelector('button[type="submit"]');

  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();

    resultado.textContent = "";
    resultado.className = "resultado-encurtar";
    botao.disabled = true;
    botao.textContent = "Criando...";

    try {
     const token = document.querySelector('meta[name="csrf-token"]').content;
     const resposta = await fetch("/links", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": token,
      },
      credentials: "same-origin",
      body: JSON.stringify({ original_url: input.value.trim() }),
    });

      if (resposta.status === 401) {
        // sessão expirou no meio do caminho
        window.location.href = "/login";
        return;
      }

      if (resposta.status === 403) {
        resultado.textContent = "Limite de links do seu plano atingido.";
        resultado.classList.add("erro");
        return;
      }

      function mostrarErro(mensagem) {
        let caixa = document.getElementById("msg-erro");
        if (!caixa) {
          caixa = document.createElement("p");
          caixa.id = "msg-erro";
          caixa.className = "msg-erro";
          document.querySelector(".card-criar-link").appendChild(caixa);
        }
        caixa.textContent = mensagem;
      }

      // Dentro do fetch, depois de receber a resposta:
      if (response.status === 401) {
        window.location.href = "/login";
        return;
      }

      if (!response.ok) {
        let mensagem = "Algo deu errado. Tente novamente.";
        try {
          const dados = await response.json();
          if (dados.erro) mensagem = dados.erro;
        } catch (e) {}
        mostrarErro(mensagem);
        return;
      }

      // sucesso: recarrega a página pra lista de links vir atualizada do servidor
      window.location.reload();
    } catch (erro) {
      resultado.textContent = "Erro de conexão. Tenta de novo.";
      resultado.classList.add("erro");
      botao.disabled = false;
      botao.textContent = "Criar link";
    }
  });
})();