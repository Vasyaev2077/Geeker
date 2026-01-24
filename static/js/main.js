// Global UI helpers: theme toggle (light/dark/accessible)

(function () {
  const THEME_KEY = "geeker-theme";
  const SIDEBAR_KEY = "geeker-sidebar";

  function applyTheme(theme) {
    const body = document.body;
    body.classList.remove("theme-light", "theme-dark", "theme-accessible");
    if (theme === "dark") {
      body.classList.add("theme-dark");
    } else if (theme === "accessible") {
      body.classList.add("theme-accessible");
    } else {
      body.classList.add("theme-light");
    }
  }

  window.setTheme = function (theme) {
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (e) {}
    applyTheme(theme);
  };

  document.addEventListener("DOMContentLoaded", function () {
    let theme = "light";
    try {
      const stored = localStorage.getItem(THEME_KEY);
      if (stored) {
        theme = stored;
      }
    } catch (e) {}
    applyTheme(theme);

    // Sidebar toggle
    try {
      const storedSidebar = localStorage.getItem(SIDEBAR_KEY);
      if (storedSidebar === "collapsed") {
        document.body.classList.add("sidebar-collapsed");
      }
    } catch (e) {}

    const toggle = document.getElementById("sidebar-toggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        const body = document.body;
        const collapsed = body.classList.toggle("sidebar-collapsed");
        try {
          localStorage.setItem(SIDEBAR_KEY, collapsed ? "collapsed" : "expanded");
        } catch (e) {}
      });
    }

    // Library search toggler
    const libraryFilters = document.querySelector(".library-filters");
    if (libraryFilters) {
      const searchToggle = document.getElementById("library-search-toggle");
      const searchRow = document.getElementById("library-search-row");
      const searchBack = document.getElementById("library-search-back");
      const searchClear = document.getElementById("library-search-clear");
      const searchInput = searchRow ? searchRow.querySelector("input[type='search']") : null;

      function openSearch() {
        libraryFilters.classList.add("search-open");
        if (searchInput) {
          searchInput.focus();
        }
      }

      function closeSearch() {
        libraryFilters.classList.remove("search-open");
      }

      if (searchToggle && searchRow) {
        searchToggle.addEventListener("click", openSearch);
      }
      if (searchBack) {
        searchBack.addEventListener("click", closeSearch);
      }
      if (searchClear && searchInput) {
        searchClear.addEventListener("click", function () {
          searchInput.value = "";
        });
      }
    }
  });
})();
