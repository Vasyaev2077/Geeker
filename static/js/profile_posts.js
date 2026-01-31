(function () {
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function initPostModal() {
    const modal = document.getElementById("post-modal");
    const form = document.getElementById("post-form");
    const title = document.getElementById("post-modal-title");
    const text = document.getElementById("post-text");
    const mediaInput = document.getElementById("post-media-input");
    const pickBtn = qs("[data-post-pick]");
    const preview = document.getElementById("post-media-preview");
    const openBtns = qsa("[data-open-post-modal]");
    const closeBtns = modal ? qsa("[data-post-close]", modal) : [];

    if (!modal || !form || !title || !text || !mediaInput || !pickBtn || !preview) return;

    let currentMode = "create";
    let editAction = null;
    let selectedFiles = [];
    let objectUrls = [];
    let existingMedia = []; // [{id, url}]
    let deletedExistingIds = [];

    function open() {
      modal.hidden = false;
      modal.setAttribute("aria-hidden", "false");
    }

    function close() {
      modal.hidden = true;
      modal.setAttribute("aria-hidden", "true");
    }

    function cleanupUrls() {
      objectUrls.forEach(function (u) {
        try {
          URL.revokeObjectURL(u);
        } catch (e) {}
      });
      objectUrls = [];
    }

    function syncInputFiles() {
      const dt = new DataTransfer();
      selectedFiles.forEach(function (f) {
        dt.items.add(f);
      });
      mediaInput.files = dt.files;
    }

    function renderPreview() {
      preview.innerHTML = "";
      cleanupUrls();

      const activeExisting = existingMedia.filter(function (m) {
        return deletedExistingIds.indexOf(String(m.id)) === -1;
      });

      if (!activeExisting.length && !selectedFiles.length) {
        preview.hidden = true;
        return;
      }

      // Existing images (from DB)
      activeExisting.forEach(function (m) {
        const cell = document.createElement("div");
        cell.className = "post-upload-thumb";

        const img = document.createElement("img");
        img.className = "post-upload-thumb-img";
        img.src = m.url;
        img.alt = "";
        img.setAttribute("data-lightbox-src", m.url);

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "post-upload-thumb-remove";
        remove.textContent = "×";
        remove.addEventListener("click", function (e) {
          if (e && e.stopPropagation) e.stopPropagation();
          deletedExistingIds.push(String(m.id));
          const hidden = document.getElementById("deleted-media-ids");
          if (hidden) hidden.value = deletedExistingIds.join(",");
          renderPreview();
        });

        cell.appendChild(img);
        cell.appendChild(remove);
        preview.appendChild(cell);
      });

      selectedFiles.forEach(function (file, idx) {
        const url = URL.createObjectURL(file);
        objectUrls.push(url);

        const cell = document.createElement("div");
        cell.className = "post-upload-thumb";

        const img = document.createElement("img");
        img.className = "post-upload-thumb-img";
        img.src = url;
        img.alt = "";
        img.setAttribute("data-lightbox-src", url);

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "post-upload-thumb-remove";
        remove.textContent = "×";
        remove.addEventListener("click", function (e) {
          // Prevent opening lightbox when clicking the remove button
          if (e && e.stopPropagation) e.stopPropagation();
          selectedFiles.splice(idx, 1);
          syncInputFiles();
          renderPreview();
        });

        cell.appendChild(img);
        cell.appendChild(remove);
        preview.appendChild(cell);
      });

      preview.hidden = false;
    }

    function resetForm() {
      text.value = "";
      selectedFiles = [];
      existingMedia = [];
      deletedExistingIds = [];
      mediaInput.value = "";
      renderPreview();
      autosizeTextarea(text);
      const hidden = document.getElementById("deleted-media-ids");
      if (hidden) hidden.value = "";
    }

    function setModeCreate() {
      currentMode = "create";
      title.textContent = "Новый пост";
      form.action = form.getAttribute("action") || form.action;
      editAction = null;
      resetForm();
    }

    function setModeEdit(btn) {
      currentMode = "edit";
      title.textContent = "Редактирование";
      editAction = btn.getAttribute("data-post-edit-url");
      if (editAction) form.action = editAction;
      text.value = btn.getAttribute("data-post-text") || "";
      selectedFiles = [];
      deletedExistingIds = [];
      existingMedia = [];
      const postId = btn.getAttribute("data-post-id");
      if (postId) {
        const node = document.getElementById("post-media-json-" + postId);
        if (node && node.textContent) {
          try {
            const parsed = JSON.parse(node.textContent);
            if (Array.isArray(parsed)) {
              existingMedia = parsed.filter((x) => x && x.id && x.url);
            }
          } catch (e) {}
        }
      }
      mediaInput.value = "";
      renderPreview();
      autosizeTextarea(text);
      const hidden = document.getElementById("deleted-media-ids");
      if (hidden) hidden.value = "";
    }

    pickBtn.addEventListener("click", function () {
      mediaInput.click();
    });

    mediaInput.addEventListener("change", function () {
      const files = (mediaInput.files && Array.from(mediaInput.files)) || [];
      if (!files.length) return;

      // Add new files up to 8 total (existing - deleted + new)
      const activeExistingCount = existingMedia.filter(function (m) {
        return deletedExistingIds.indexOf(String(m.id)) === -1;
      }).length;
      files.forEach(function (f) {
        if (activeExistingCount + selectedFiles.length >= 8) return;
        if (f.type && f.type.startsWith("image/")) {
          selectedFiles.push(f);
        }
      });

      syncInputFiles();
      renderPreview();
    });

    openBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        const mode = btn.getAttribute("data-open-post-modal");
        if (mode === "edit") {
          setModeEdit(btn);
        } else {
          setModeCreate();
        }
        open();
        autosizeTextarea(text);
      });
    });

    closeBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        close();
      });
    });

    // Close on Esc
    window.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !modal.hidden) {
        close();
      }
    });

    // On submit, keep currentMode; server redirects back to feed
    form.addEventListener("submit", function () {
      if (currentMode === "edit" && editAction) {
        form.action = editAction;
      }
    });
  }

  function autosizeTextarea(el) {
    if (!el) return;
    const maxH = 180; // grow "резиной" until this height, then enable scroll
    el.style.height = "auto";
    const minH = parseFloat(getComputedStyle(el).minHeight || "0") || 0;
    const next = Math.min(Math.max(el.scrollHeight, minH), maxH);
    el.style.height = next + "px";
    el.style.overflowY = el.scrollHeight > maxH ? "auto" : "hidden";
  }

  function initPostTextareaAutosize() {
    const el = document.getElementById("post-text");
    if (!el) return;
    autosizeTextarea(el);
    el.addEventListener("input", function () {
      autosizeTextarea(el);
    });
  }

  function initDeleteConfirm() {
    document.addEventListener("click", function (e) {
      const btn = e.target && e.target.closest && e.target.closest("[data-confirm-delete]");
      if (!btn) return;
      const ok = window.confirm("Ты точно уверен(а), что хочешь удалить этот пост?");
      if (!ok) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  }

  function initPostMenu() {
    // Toggle dropdown, close on outside click
    document.addEventListener("click", function (e) {
      const btn = e.target && e.target.closest && e.target.closest("[data-post-menu-btn]");
      const dropdowns = qsa(".post-menu-dropdown");

      if (!btn) {
        dropdowns.forEach(function (d) {
          d.hidden = true;
        });
        return;
      }

      const menu = btn.parentElement;
      const dropdown = qs(".post-menu-dropdown", menu);
      if (!dropdown) return;

      dropdowns.forEach(function (d) {
        if (d !== dropdown) d.hidden = true;
      });
      dropdown.hidden = !dropdown.hidden;
      e.preventDefault();
      e.stopPropagation();
    });
  }

  function initLightbox() {
    const box = document.getElementById("lightbox");
    const img = document.getElementById("lightbox-img");
    const counter = document.getElementById("lightbox-counter");
    if (!box || !img) return;

    let sources = [];
    let idx = 0;

    function render() {
      img.src = sources[idx] || "";
      if (counter) {
        counter.textContent = sources.length > 1 ? `${idx + 1} / ${sources.length}` : "";
      }
    }

    function open(list, startIdx) {
      sources = list || [];
      idx = Math.max(0, Math.min(startIdx || 0, sources.length - 1));
      render();
      box.hidden = false;
      box.setAttribute("aria-hidden", "false");
      document.body.classList.add("modal-open");
    }

    function close() {
      box.hidden = true;
      box.setAttribute("aria-hidden", "true");
      img.src = "";
      if (counter) counter.textContent = "";
      sources = [];
      idx = 0;
      document.body.classList.remove("modal-open");
    }

    document.addEventListener("click", function (e) {
      const t = e.target;
      const lb = t && t.closest && t.closest("[data-carousel-img]");
      if (lb) {
        const postId = lb.getAttribute("data-post-id");
        const start = parseInt(lb.getAttribute("data-index") || "0", 10) || 0;
        const list = Array.from(
          document.querySelectorAll(`.post-carousel-img[data-post-id="${postId}"]`)
        ).map((n) => n.getAttribute("src"));
        open(list, start);
        return;
      }

      const single = t && t.closest && t.closest("[data-lightbox-src]");
      if (single) {
        open([single.getAttribute("data-lightbox-src")], 0);
        return;
      }

      const closeBtn = t && t.closest && t.closest("[data-lightbox-close]");
      if (closeBtn && !box.hidden) {
        close();
      }

      const prevBtn = t && t.closest && t.closest("[data-lightbox-prev]");
      if (prevBtn && sources.length) {
        idx = (idx - 1 + sources.length) % sources.length;
        render();
      }

      const nextBtn = t && t.closest && t.closest("[data-lightbox-next]");
      if (nextBtn && sources.length) {
        idx = (idx + 1) % sources.length;
        render();
      }
    });

    window.addEventListener("keydown", function (e) {
      if (box.hidden) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft" && sources.length) {
        idx = (idx - 1 + sources.length) % sources.length;
        render();
      }
      if (e.key === "ArrowRight" && sources.length) {
        idx = (idx + 1) % sources.length;
        render();
      }
    });
  }

  function initCarousels() {
    qsa("[data-carousel]").forEach(function (carousel) {
      const track = qs(".post-carousel-track", carousel);
      const slides = qsa(".post-carousel-slide", carousel);
      const dotsWrap = qs("[data-carousel-dots]", carousel);
      const dots = dotsWrap ? qsa("[data-carousel-dot]", dotsWrap) : [];
      const prev = qs("[data-carousel-prev]", carousel);
      const next = qs("[data-carousel-next]", carousel);
      if (!track || !slides.length) return;

      let idx = 0;

      function render() {
        track.style.transform = `translateX(${-idx * 100}%)`;
        dots.forEach(function (d) {
          d.classList.toggle("post-carousel-dot-active", (parseInt(d.getAttribute("data-index") || "0", 10) || 0) === idx);
        });
      }

      function setIndex(i) {
        idx = Math.max(0, Math.min(i, slides.length - 1));
        render();
      }

      if (prev) {
        prev.addEventListener("click", function () {
          setIndex((idx - 1 + slides.length) % slides.length);
        });
      }
      if (next) {
        next.addEventListener("click", function () {
          setIndex((idx + 1) % slides.length);
        });
      }
      dots.forEach(function (d) {
        d.addEventListener("click", function () {
          setIndex(parseInt(d.getAttribute("data-index") || "0", 10) || 0);
        });
      });

      render();
    });
  }

  function initPostTextToggle() {
    document.addEventListener("click", function (e) {
      const btn = e.target && e.target.closest && e.target.closest("[data-post-text-toggle]");
      if (!btn) return;
      const wrap = btn.closest(".post-text");
      if (!wrap) return;
      const shortEl = qs(".post-text-short", wrap);
      const fullEl = qs(".post-text-full", wrap);
      if (!shortEl || !fullEl) return;
      const expanded = !fullEl.hidden;
      fullEl.hidden = expanded;
      shortEl.hidden = !expanded;
      btn.textContent = expanded ? "Развернуть" : "Свернуть";
    });
  }

  function initCommentsToggle() {
    document.addEventListener("click", function (e) {
      const btn = e.target && e.target.closest && e.target.closest("[data-post-comments-toggle]");
      if (!btn) return;
      const card = btn.closest(".post-card");
      if (!card) return;
      const block = qs(".post-comments", card);
      if (!block) return;
      block.hidden = !block.hidden;
    });
  }

  function initShare() {
    document.addEventListener("click", async function (e) {
      const btn = e.target && e.target.closest && e.target.closest("[data-post-share]");
      if (!btn) return;
      const anchor = btn.getAttribute("data-post-share-url") || "";
      const url = window.location.origin + window.location.pathname + window.location.search + anchor;
      try {
        await navigator.clipboard.writeText(url);
        btn.textContent = "✓ Скопировано";
        setTimeout(function () {
          btn.textContent = "↗ Поделиться";
        }, 1200);
      } catch (err) {
        window.prompt("Скопируйте ссылку:", url);
      }
    });
  }

  function getCookie(name) {
    const value = `; ${document.cookie || ""}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  function initVoteAjax() {
    document.addEventListener("submit", async function (e) {
      const form = e.target;
      if (!form || !form.closest) return;
      const wrap = form.closest(".post-votes");
      if (!wrap) return;

      e.preventDefault();

      const fd = new FormData(form);
      const csrf = getCookie("csrftoken");

      try {
        const res = await fetch(form.action, {
          method: "POST",
          body: fd,
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
            ...(csrf ? { "X-CSRFToken": csrf } : {}),
          },
        });
        const data = await res.json();
        if (!data || !data.ok) return;

        const scoreEl = qs(".post-vote-score", wrap);
        if (scoreEl) scoreEl.textContent = String(data.score);

        const upBtn = qs('[data-vote-btn="1"]', wrap);
        const downBtn = qs('[data-vote-btn="-1"]', wrap);
        if (upBtn) upBtn.classList.toggle("post-vote-active", data.user_vote === 1);
        if (downBtn) downBtn.classList.toggle("post-vote-active", data.user_vote === -1);
      } catch (err) {
        // fallback: allow normal submit if something goes wrong
        try {
          form.submit();
        } catch (e2) {}
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initPostModal();
    initPostMenu();
    initLightbox();
    initPostTextareaAutosize();
    initDeleteConfirm();
    initCarousels();
    initPostTextToggle();
    initCommentsToggle();
    initShare();
    initVoteAjax();
  });
})();

