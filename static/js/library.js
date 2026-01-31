(function () {
  function qs(root, sel) {
    return root ? root.querySelector(sel) : null;
  }

  // Lightbox for item media
  function initLightbox() {
    // Create once
    if (window.LibraryLightbox && window.LibraryLightbox.open) return;

    const overlay = document.createElement("div");
    overlay.className = "library-lightbox";
    overlay.innerHTML = `
      <div class="library-lightbox__backdrop" data-close></div>
      <div class="library-lightbox__dialog" role="dialog" aria-modal="true">
        <button class="library-lightbox__close" type="button" data-close aria-label="Close">✕</button>
        <button class="library-lightbox__nav library-lightbox__nav--prev" type="button" data-prev aria-label="Previous">‹</button>
        <img class="library-lightbox__img" alt="">
        <button class="library-lightbox__nav library-lightbox__nav--next" type="button" data-next aria-label="Next">›</button>
      </div>
    `;
    document.body.appendChild(overlay);

    const imgEl = qs(overlay, ".library-lightbox__img");
    let sources = [];
    let idx = 0;

    function openWith(newSources, startIdx) {
      sources = Array.isArray(newSources) ? newSources.filter(Boolean) : [];
      if (!sources.length) return;
      idx = Math.max(0, Math.min(sources.length - 1, startIdx || 0));
      if (imgEl) imgEl.src = sources[idx] || "";
      overlay.classList.add("is-open");
      document.body.classList.add("modal-open");
    }

    function close() {
      overlay.classList.remove("is-open");
      document.body.classList.remove("modal-open");
      if (imgEl) imgEl.src = "";
      sources = [];
    }

    function prev() {
      if (!sources.length) return;
      openWith(sources, (idx - 1 + sources.length) % sources.length);
    }
    function next() {
      if (!sources.length) return;
      openWith(sources, (idx + 1) % sources.length);
    }

    // Delegated clicks: any element with [data-gallery-item] opens the lightbox
    document.addEventListener("click", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      const el = t.closest("[data-gallery-item]");
      if (!el) return;
      e.preventDefault();

      const group = el.getAttribute("data-gallery-group") || "";
      const items = Array.from(
        document.querySelectorAll(group ? `[data-gallery-item][data-gallery-group="${group}"]` : "[data-gallery-item]")
      );
      const i = items.indexOf(el);
      const srcs = items
        .map((x) => x.getAttribute("data-fullsrc") || x.getAttribute("href"))
        .filter(Boolean);
      openWith(srcs, i >= 0 ? i : 0);
    });

    overlay.addEventListener("click", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      if (t.hasAttribute("data-close")) close();
    });

    const prevBtn = qs(overlay, "[data-prev]");
    const nextBtn = qs(overlay, "[data-next]");
    if (prevBtn) prevBtn.addEventListener("click", prev);
    if (nextBtn) nextBtn.addEventListener("click", next);

    document.addEventListener("keydown", (e) => {
      if (!overlay.classList.contains("is-open")) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    });

    window.LibraryLightbox = { open: openWith, close: close };
  }

  // Metadata editor: key/value rows -> JSON hidden input
  function initMetadataEditor() {
    const root = document.querySelector("[data-metadata-editor]");
    if (!root) return;

    const hidden = qs(root, "input[type='hidden'][data-metadata-json]");
    const list = qs(root, "[data-metadata-rows]");
    const addBtn = qs(root, "[data-metadata-add]");

    if (!hidden || !list || !addBtn) return;

    function rowTemplate(key, value) {
      const row = document.createElement("div");
      row.className = "metadata-row";
      row.innerHTML = `
        <input class="metadata-key" type="text" placeholder="Название поля (например: Автор)" value="">
        <input class="metadata-value" type="text" placeholder="Значение (например: Стивен Кинг)" value="">
        <button type="button" class="metadata-remove" aria-label="Удалить">✕</button>
      `;
      const keyEl = qs(row, ".metadata-key");
      const valEl = qs(row, ".metadata-value");
      if (keyEl) keyEl.value = key || "";
      if (valEl) valEl.value = value || "";
      const rm = qs(row, ".metadata-remove");
      if (rm) rm.addEventListener("click", () => {
        row.remove();
        sync();
      });
      row.addEventListener("input", sync);
      return row;
    }

    function sync() {
      const obj = {};
      const rows = Array.from(list.querySelectorAll(".metadata-row"));
      rows.forEach((r) => {
        const k = (qs(r, ".metadata-key")?.value || "").trim();
        const v = (qs(r, ".metadata-value")?.value || "").trim();
        if (k) obj[k] = v;
      });
      hidden.value = JSON.stringify(obj);
    }

    function loadFromHidden() {
      list.innerHTML = "";
      let obj = {};
      try {
        obj = JSON.parse(hidden.value || "{}") || {};
      } catch (e) {
        obj = {};
      }
      const entries = Object.entries(obj);
      if (!entries.length) {
        list.appendChild(rowTemplate("", ""));
      } else {
        entries.forEach(([k, v]) => list.appendChild(rowTemplate(k, String(v))));
      }
      sync();
    }

    addBtn.addEventListener("click", () => {
      list.appendChild(rowTemplate("", ""));
      sync();
    });

    loadFromHidden();
  }

  // Upload previews + choose primary among NEW uploads
  function initUploadPreviews() {
    const input = document.getElementById("id_images");
    const grid = document.getElementById("library-upload-previews");
    const hiddenPrimary = document.getElementById("primary_upload_idx");
    const hiddenOverride = document.getElementById("primary_upload_override");
    const pickedLabel = document.getElementById("images-picked-label");
    const addMoreBtn = document.getElementById("images-add-more");
    const clearBtn = document.getElementById("images-clear");
    const emptyHint = document.getElementById("upload-preview-empty");
    if (!input || !grid || !hiddenPrimary) return;

    let files = [];
    let primaryIdx = 0;
    let objectUrls = [];

    function revokeAll() {
      objectUrls.forEach((u) => {
        try {
          URL.revokeObjectURL(u);
        } catch (e) {}
      });
      objectUrls = [];
    }

    function setFilesToInput(newFiles) {
      const dt = new DataTransfer();
      newFiles.forEach((f) => dt.items.add(f));
      input.files = dt.files;
    }

    function render() {
      revokeAll();
      grid.innerHTML = "";
      if (!files.length) {
        grid.classList.remove("is-open");
        hiddenPrimary.value = "";
        if (hiddenOverride) hiddenOverride.value = "";
        if (pickedLabel) pickedLabel.textContent = "Не выбрано";
        if (addMoreBtn) addMoreBtn.style.display = "none";
        if (clearBtn) clearBtn.style.display = "none";
        if (emptyHint) emptyHint.style.display = "block";
        // re-enable existing primary radios if present
        document.querySelectorAll('input[name="primary_media_id"]').forEach((el) => {
          try {
            el.disabled = false;
          } catch (e) {}
        });
        return;
      }
      grid.classList.add("is-open");
      primaryIdx = Math.max(0, Math.min(primaryIdx, files.length - 1));
      hiddenPrimary.value = String(primaryIdx);
      if (pickedLabel) pickedLabel.textContent = `Выбрано: ${files.length}`;
      if (addMoreBtn) addMoreBtn.style.display = "";
      if (clearBtn) clearBtn.style.display = "";
      if (emptyHint) emptyHint.style.display = "none";

      // Pre-create URLs so we can open in a lightbox reliably
      objectUrls = files.map((f) => URL.createObjectURL(f));

      const main = document.createElement("div");
      main.className = "upload-preview-main";
      const mainImg = document.createElement("img");
      mainImg.alt = files[primaryIdx]?.name || "";
      mainImg.src = objectUrls[primaryIdx] || "";
      main.appendChild(mainImg);

      const prevBtn = document.createElement("button");
      prevBtn.type = "button";
      prevBtn.className = "upload-preview-nav prev";
      prevBtn.textContent = "‹";
      prevBtn.addEventListener("click", () => {
        if (hiddenOverride) hiddenOverride.value = "1";
        document.querySelectorAll('input[name="primary_media_id"]').forEach((el) => {
          try {
            el.disabled = true;
          } catch (e) {}
        });
        primaryIdx = (primaryIdx - 1 + files.length) % files.length;
        hiddenPrimary.value = String(primaryIdx);
        render();
      });

      const nextBtn = document.createElement("button");
      nextBtn.type = "button";
      nextBtn.className = "upload-preview-nav next";
      nextBtn.textContent = "›";
      nextBtn.addEventListener("click", () => {
        if (hiddenOverride) hiddenOverride.value = "1";
        document.querySelectorAll('input[name="primary_media_id"]').forEach((el) => {
          try {
            el.disabled = true;
          } catch (e) {}
        });
        primaryIdx = (primaryIdx + 1) % files.length;
        hiddenPrimary.value = String(primaryIdx);
        render();
      });

      main.appendChild(prevBtn);
      main.appendChild(nextBtn);

      // Click main image: open viewer with arrows
      main.addEventListener("click", () => {
        if (window.LibraryLightbox && window.LibraryLightbox.open) {
          window.LibraryLightbox.open(objectUrls, primaryIdx);
        }
      });

      const thumbs = document.createElement("div");
      thumbs.className = "upload-preview-thumbs";

      files.forEach((file, idx) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "upload-thumb" + (idx === primaryIdx ? " is-active" : "");
        b.title = "Сделать обложкой";
        const img = document.createElement("img");
        img.alt = file.name;
        img.src = objectUrls[idx] || "";
        b.appendChild(img);
        b.addEventListener("click", () => {
          if (hiddenOverride) hiddenOverride.value = "1";
          // disable existing primary radios so update view can pick new cover cleanly
          document.querySelectorAll('input[name="primary_media_id"]').forEach((el) => {
            try {
              el.disabled = true;
            } catch (e) {}
          });
          primaryIdx = idx;
          hiddenPrimary.value = String(primaryIdx);
          render();
        });

        const rm = document.createElement("button");
        rm.type = "button";
        rm.className = "upload-thumb-remove";
        rm.textContent = "✕";
        rm.title = "Убрать";
        rm.addEventListener("click", (e) => {
          e.stopPropagation();
          files.splice(idx, 1);
          if (primaryIdx >= files.length) primaryIdx = files.length - 1;
          if (primaryIdx < 0) primaryIdx = 0;
          setFilesToInput(files);
          render();
        });
        b.appendChild(rm);

        thumbs.appendChild(b);
      });

      grid.appendChild(main);
      grid.appendChild(thumbs);
    }

    input.addEventListener("change", () => {
      const selected = Array.from(input.files || []);
      if (!selected.length) return;

      // Browsers replace the FileList on every pick; we keep our own `files`
      // and merge new picks into it (up to 10), deduping by name/size/lastModified.
      const keyOf = (f) => `${f.name}::${f.size}::${f.lastModified}`;
      const seen = new Set(files.map(keyOf));
      const merged = [...files];
      selected.forEach((f) => {
        const k = keyOf(f);
        if (seen.has(k)) return;
        seen.add(k);
        merged.push(f);
      });

      files = merged.slice(0, 10);
      if (files.length && hiddenPrimary.value === "") primaryIdx = 0;
      if (primaryIdx >= files.length) primaryIdx = files.length - 1;
      if (primaryIdx < 0) primaryIdx = 0;
      setFilesToInput(files);
      render();
    });

    if (addMoreBtn) {
      addMoreBtn.addEventListener("click", () => {
        input.click();
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        files = [];
        primaryIdx = 0;
        setFilesToInput(files);
        render();
      });
    }

    // initial state
    if (pickedLabel) pickedLabel.textContent = "Не выбрано";
    if (addMoreBtn) addMoreBtn.style.display = "none";
    if (clearBtn) clearBtn.style.display = "none";
    if (hiddenOverride) hiddenOverride.value = "";
  }

  // Reuse "post" carousel behavior (track translateX + dots + arrows)
  function initCarousels() {
    const carousels = Array.from(document.querySelectorAll("[data-carousel]"));
    if (!carousels.length) return;

    function qs(root, sel) {
      return root ? root.querySelector(sel) : null;
    }
    function qsa(root, sel) {
      return root ? Array.from(root.querySelectorAll(sel)) : [];
    }

    carousels.forEach(function (carousel) {
      const track = qs(carousel, ".post-carousel-track");
      const slides = qsa(carousel, ".post-carousel-slide");
      const dotsWrap = qs(carousel, "[data-carousel-dots]");
      const dots = dotsWrap ? qsa(dotsWrap, "[data-carousel-dot]") : [];
      const prev = qs(carousel, "[data-carousel-prev]");
      const next = qs(carousel, "[data-carousel-next]");
      if (!track || !slides.length) return;

      let idx = 0;

      function render() {
        track.style.transform = `translateX(${-idx * 100}%)`;
        dots.forEach(function (d) {
          const i = parseInt(d.getAttribute("data-index") || "0", 10) || 0;
          d.classList.toggle("post-carousel-dot-active", i === idx);
        });
        // hide arrows/dots when only 1 slide
        const many = slides.length > 1;
        if (prev) prev.style.display = many ? "" : "none";
        if (next) next.style.display = many ? "" : "none";
        if (dotsWrap) dotsWrap.style.display = many ? "" : "none";

        carousel.dataset.carouselIndex = String(idx);
        try {
          carousel.dispatchEvent(new CustomEvent("carousel:change", { detail: { index: idx } }));
        } catch (e) {}
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

  // Item edit form: existing media carousel + actions (make primary / delete current)
  function initExistingMediaControls() {
    const carousel = document.querySelector("[data-item-existing-carousel]");
    const actions = document.querySelector("[data-item-existing-actions]");
    if (!carousel || !actions) return;

    const makePrimaryBtn = actions.querySelector("[data-existing-make-primary]");
    const deleteToggle = actions.querySelector("[data-existing-delete-current]");
    const radios = Array.from(actions.querySelectorAll("[data-existing-primary-radio]"));
    const deletes = Array.from(actions.querySelectorAll("[data-existing-delete-checkbox]"));

    // Keep real inputs hidden but submittable
    radios.forEach((el) => (el.style.display = "none"));
    deletes.forEach((el) => (el.style.display = "none"));

    function getIdx() {
      return parseInt(carousel.dataset.carouselIndex || "0", 10) || 0;
    }

    function syncUiFromIdx() {
      const idx = getIdx();
      const del = deletes.find((x) => (parseInt(x.getAttribute("data-index") || "0", 10) || 0) === idx);
      const rad = radios.find((x) => (parseInt(x.getAttribute("data-index") || "0", 10) || 0) === idx);
      if (deleteToggle && del) deleteToggle.checked = !!del.checked;
      if (makePrimaryBtn && rad) {
        makePrimaryBtn.textContent = rad.checked ? "Обложка" : "Сделать обложкой";
      }
    }

    if (makePrimaryBtn) {
      makePrimaryBtn.addEventListener("click", () => {
        // user explicitly wants an existing cover -> allow existing radios again and clear new override
        const hiddenOverride = document.getElementById("primary_upload_override");
        if (hiddenOverride) hiddenOverride.value = "";
        document.querySelectorAll('input[name="primary_media_id"]').forEach((el) => {
          try {
            el.disabled = false;
          } catch (e) {}
        });
        const idx = getIdx();
        const rad = radios.find((x) => (parseInt(x.getAttribute("data-index") || "0", 10) || 0) === idx);
        if (rad) rad.checked = true;
        syncUiFromIdx();
      });
    }

    if (deleteToggle) {
      deleteToggle.addEventListener("change", () => {
        const idx = getIdx();
        const del = deletes.find((x) => (parseInt(x.getAttribute("data-index") || "0", 10) || 0) === idx);
        if (del) del.checked = !!deleteToggle.checked;
      });
    }

    carousel.addEventListener("carousel:change", syncUiFromIdx);

    // Initial sync
    syncUiFromIdx();
  }

  // Simple char counters for inputs/textareas with data-char-limit
  function initCharCounters() {
    const fields = Array.from(document.querySelectorAll("textarea[data-char-limit], input[data-char-limit]"));
    if (!fields.length) return;

    fields.forEach((el) => {
      const limit = parseInt(el.getAttribute("data-char-limit") || "0", 10) || 0;
      if (!limit) return;
      const id = el.getAttribute("id") || "";
      const counter = document.querySelector(`[data-char-counter][data-for="${id}"]`);
      const cur = counter ? counter.querySelector("[data-char-current]") : null;
      const lim = counter ? counter.querySelector("[data-char-limit]") : null;
      if (lim) lim.textContent = String(limit);

      function update() {
        const len = (el.value || "").length;
        if (cur) cur.textContent = String(len);
      }

      el.addEventListener("input", update);
      update();
    });
  }

  function initSectionCoverPreview() {
    const input = document.getElementById("id_cover");
    const box = document.getElementById("section-cover-live");
    const img = document.getElementById("section-cover-live-img");
    if (!input || !box || !img) return;

    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) {
        box.style.display = "none";
        img.src = "";
        return;
      }
      const url = URL.createObjectURL(file);
      img.src = url;
      box.style.display = "block";
      img.onload = () => {
        try {
          URL.revokeObjectURL(url);
        } catch (e) {}
      };
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initLightbox();
    initMetadataEditor();
    initUploadPreviews();
    initCarousels();
    initExistingMediaControls();
    initCharCounters();
    initSectionCoverPreview();
  });
})();

