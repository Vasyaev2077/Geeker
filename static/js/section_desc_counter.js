(function () {
  function initSectionDescCounter() {
    const counters = Array.from(document.querySelectorAll("[data-char-counter]"));
    counters.forEach(function (wrap) {
      const forId = wrap.getAttribute("data-for");
      const max = parseInt(wrap.getAttribute("data-max") || "50", 10) || 50;
      const input = forId ? document.getElementById(forId) : null;
      const current = wrap.querySelector("[data-current]");
      if (!input || !current) return;

      function render() {
        const len = (input.value || "").length;
        current.textContent = String(len);
        if (len >= max) {
          wrap.style.color = "#ef4444";
        } else {
          wrap.style.color = "";
        }
      }

      input.addEventListener("input", render);
      render();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSectionDescCounter();
  });
})();

