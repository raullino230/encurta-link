(function () {
  const botao = document.getElementById("btn-menu-mobile");
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.getElementById("overlay-sidebar");

  // essas três coisas só existem nas páginas internas (dashboard/analytics/configurações)
  if (!botao || !sidebar || !overlay) return;

  function abrirMenu() {
    sidebar.classList.add("aberta");
    overlay.classList.add("aberto");
  }

  function fecharMenu() {
    sidebar.classList.remove("aberta");
    overlay.classList.remove("aberto");
  }

  botao.addEventListener("click", function () {
    // se já está aberta, fecha; senão, abre (alterna)
    if (sidebar.classList.contains("aberta")) {
      fecharMenu();
    } else {
      abrirMenu();
    }
  });

  // clicar fora (no overlay escuro) fecha o menu
  overlay.addEventListener("click", fecharMenu);

  // clicar em qualquer link do menu também fecha
  // (a página vai navegar de qualquer forma, mas evita o menu ficar "aberto"
  // visualmente por uma fração de segundo antes da navegação)
  sidebar.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", fecharMenu);
  });
})();