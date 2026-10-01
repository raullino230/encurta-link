(function () {
  const form = document.getElementById("form-encurtar");
  if (!form) return; // só existe na landing page

  form.addEventListener("submit", function (evento) {
    evento.preventDefault(); // não deixa o form fazer POST direto pra /links
    window.location.href = "/login";
  });
})();