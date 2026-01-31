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

<<<<<<< HEAD
    // Expose navbar height to CSS so sidebar can stick correctly everywhere
    function syncNavbarHeight() {
      const nav = document.querySelector(".navbar");
      const h = nav ? nav.offsetHeight || 0 : 0;
      document.documentElement.style.setProperty("--navbar-h", `${h}px`);
    }
    syncNavbarHeight();
    window.addEventListener("resize", syncNavbarHeight);

    // Theme toggle button (light <-> dark)
    const themeToggle = document.getElementById("theme-toggle");
    function currentTheme() {
      if (document.body.classList.contains("theme-dark")) return "dark";
      if (document.body.classList.contains("theme-accessible")) return "accessible";
      return "light";
    }
    function updateThemeIcon() {
      if (!themeToggle) return;
      const t = currentTheme();
      const svg = themeToggle.querySelector("svg");
      if (!svg) return;
      if (t === "dark") {
        svg.innerHTML =
          '<circle cx="12" cy="12" r="5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>';
      } else {
        svg.innerHTML =
          '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 1 0 9.8 9.8Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
      }
    }
    if (themeToggle) {
      themeToggle.addEventListener("click", function () {
        const t = currentTheme();
        window.setTheme(t === "dark" ? "light" : "dark");
        updateThemeIcon();
      });
      updateThemeIcon();
    }

=======
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753
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
<<<<<<< HEAD
      const orderSelect = libraryFilters.querySelector("select[name='order']");
      const advancedToggle = libraryFilters.querySelector("input[name='advanced']");
      const descOnlyToggle = libraryFilters.querySelector("input[name='search_in_description']");
      const sectionCheckboxes = Array.from(libraryFilters.querySelectorAll("input[name='sections']"));
=======
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753

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
<<<<<<< HEAD
          scheduleSubmit();
        });
      }

      // Auto-submit on filters change (quick UX)
      let submitTimer = null;
      function scheduleSubmit() {
        if (submitTimer) {
          clearTimeout(submitTimer);
        }
        submitTimer = setTimeout(function () {
          libraryFilters.submit();
        }, 150);
      }

      if (orderSelect) {
        orderSelect.addEventListener("change", scheduleSubmit);
      }
      if (advancedToggle) {
        advancedToggle.addEventListener("change", scheduleSubmit);
      }
      if (descOnlyToggle) {
        descOnlyToggle.addEventListener("change", scheduleSubmit);
      }
      sectionCheckboxes.forEach(function (cb) {
        cb.addEventListener("change", scheduleSubmit);
      });
      if (searchInput) {
        searchInput.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            e.preventDefault();
            scheduleSubmit();
          }
        });
      }

    }

    // Section detail: search toggler (no "back" button)
    const sectionSearch = document.querySelector(".section-search");
    if (sectionSearch) {
      const toggleBtn = document.getElementById("section-search-toggle");
      const row = document.getElementById("section-search-row");
      const clearBtn = document.getElementById("section-search-clear");
      const advBtn = document.getElementById("section-adv-toggle");
      const advMenu = document.getElementById("section-adv-menu");
      const orderSelect = document.getElementById("section-order-select");
      const input = row ? row.querySelector('input[type="search"]') : null;

      function open() {
        sectionSearch.classList.add("search-open");
        if (input) input.focus();
      }
      function close() {
        sectionSearch.classList.remove("search-open");
      }

      if (toggleBtn && row) {
        toggleBtn.addEventListener("click", function () {
          if (sectionSearch.classList.contains("search-open")) close();
          else open();
        });
      }

      function toggleAdv(forceOpen) {
        if (!advMenu) return;
        const shouldOpen = forceOpen !== undefined ? !!forceOpen : advMenu.hidden;
        advMenu.hidden = !shouldOpen;
      }

      if (advBtn) {
        advBtn.addEventListener("click", function (e) {
          if (e && e.preventDefault) e.preventDefault();
          if (e && e.stopPropagation) e.stopPropagation();
          toggleAdv();
        });
      }

      if (orderSelect) {
        orderSelect.addEventListener("change", function () {
          sectionSearch.submit();
        });
      }

      if (clearBtn && input) {
        clearBtn.addEventListener("click", function () {
          input.value = "";
          sectionSearch.submit();
        });
      }

      if (input) {
        input.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            e.preventDefault();
            sectionSearch.submit();
          }
          if (e.key === "Escape") {
            close();
            toggleAdv(false);
          }
        });
      }

      // Click outside closes advanced menu
      document.addEventListener("click", function (e) {
        if (!advMenu || advMenu.hidden) return;
        const inside =
          e.target &&
          e.target.closest &&
          (e.target.closest("#section-adv-menu") || e.target.closest("#section-adv-toggle"));
        if (!inside) toggleAdv(false);
      });

      // auto-open if query exists
      if (input && (input.value || "").trim()) open();
    }

    // Generic kebab menus (e.g. section cards)
    function closeAllMenus(exceptDropdown) {
      Array.from(document.querySelectorAll("[data-menu-dropdown]")).forEach(function (d) {
        if (exceptDropdown && d === exceptDropdown) return;
        d.hidden = true;
      });
    }

    // Attach explicit handlers for reliability (prevents link overlays stealing click)
    Array.from(document.querySelectorAll("[data-menu-btn]")).forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        if (e && e.preventDefault) e.preventDefault();
        if (e && e.stopPropagation) e.stopPropagation();

        const menu = btn.closest(".post-menu") || btn.parentElement;
        const dropdown = menu ? menu.querySelector("[data-menu-dropdown]") : null;
        if (!dropdown) return;

        const isOpen = dropdown.hidden === false;
        closeAllMenus(isOpen ? null : dropdown);
        dropdown.hidden = isOpen ? true : false;
      });
    });

    // Click outside closes menus
    document.addEventListener("click", function (e) {
      const insideMenu =
        e.target &&
        e.target.closest &&
        (e.target.closest(".post-menu-dropdown") || e.target.closest("[data-menu-btn]"));
      if (insideMenu) return;
      closeAllMenus(null);
    });

    // Post-like "Развернуть / Свернуть" for any .post-text blocks (used in profile posts and library item cards)
    document.addEventListener("click", function (e) {
      const btn = e.target && e.target.closest && e.target.closest("[data-post-text-toggle]");
      if (!btn) return;
      const wrap = btn.closest(".post-text");
      if (!wrap) return;
      const shortEl = wrap.querySelector(".post-text-short");
      const fullEl = wrap.querySelector(".post-text-full");
      if (!shortEl || !fullEl) return;
      const expanded = !fullEl.hidden;
      fullEl.hidden = expanded;
      shortEl.hidden = !expanded;
      btn.textContent = expanded ? "Развернуть" : "Свернуть";
      e.preventDefault();
      e.stopPropagation();
    });

    // Item "Move to another section" modal
    (function initItemMoveModal() {
      const modal = document.getElementById("item-move-modal");
      const form = document.getElementById("item-move-form");
      if (!modal || !form) return;

      function open(url) {
        if (!url) return;
        form.setAttribute("action", url);
        modal.hidden = false;
        document.body.classList.add("modal-open");
      }
      function close() {
        modal.hidden = true;
        document.body.classList.remove("modal-open");
      }

      document.addEventListener("click", function (e) {
        const btn = e.target && e.target.closest && e.target.closest("[data-item-move-btn]");
        if (btn) {
          const url = btn.getAttribute("data-move-url") || "";
          open(url);
          e.preventDefault();
          e.stopPropagation();
          return;
        }
        const closeBtn = e.target && e.target.closest && e.target.closest("[data-item-move-close]");
        if (closeBtn && !modal.hidden) {
          close();
          e.preventDefault();
          e.stopPropagation();
          return;
        }
      });

      window.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && !modal.hidden) close();
      });
    })();
=======
        });
      }
    }
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753
  });
})();
