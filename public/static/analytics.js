// Seletor de link do Analytics (só Pro): recarrega a página mantendo
// o período (e qualquer outro parâmetro) que já está na URL.
document.addEventListener("change", function (evento) {
  if (evento.target.id !== "seletor-link") return;

  var parametros = new URLSearchParams(window.location.search);
  if (evento.target.value) {
    parametros.set("link", evento.target.value);
  } else {
    parametros.delete("link");
  }
  window.location.search = parametros.toString();
});