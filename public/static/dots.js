(function () {
  const canvas = document.getElementById("dots-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const spacing = 26;
  const mouse = { x: -1000, y: -1000 };

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });
  window.addEventListener("mouseleave", () => {
    mouse.x = -1000;
    mouse.y = -1000;
  });

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (let x = spacing / 2; x < canvas.width; x += spacing) {
      for (let y = spacing / 2; y < canvas.height; y += spacing) {
        const dx = x - mouse.x;
        const dy = y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const influence = Math.max(0, 1 - dist / 160);

        const radius = 1 + influence * 1.8;
        const alpha = 0.12 + influence * 0.7;

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(57, 211, 83, ${alpha.toFixed(2)})`;
        ctx.fill();
      }
    }

    requestAnimationFrame(draw);
  }

  draw();
})();