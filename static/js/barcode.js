(function () {
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function getCookie(name) {
    const value = `; ${document.cookie || ""}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  async function fetchJson(url, bodyObj) {
    const csrf = getCookie("csrftoken");
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(csrf ? { "X-CSRFToken": csrf } : {}),
      },
      body: JSON.stringify(bodyObj || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data && data.error ? data.error : "lookup_failed");
    return data;
  }

  function normalizeCode(s) {
    const raw = (s || "").trim();
    return raw.replace(/[^0-9Xx]/g, "").toUpperCase();
  }

  function setText(el, txt) {
    if (!el) return;
    el.textContent = txt || "";
  }

  function show(el, yes) {
    if (!el) return;
    el.hidden = !yes;
  }

  async function decodeFromImageFile(file) {
    if (!file) return "";
    // Prefer native BarcodeDetector if available, fallback to ZXing.
    if ("BarcodeDetector" in window) {
      const types = ["ean_13", "ean_8", "upc_a", "code_128", "qr_code"];
      const detector = new window.BarcodeDetector({ formats: types });
      const bmp = await createImageBitmap(file);
      const codes = await detector.detect(bmp);
      if (codes && codes[0] && codes[0].rawValue) return String(codes[0].rawValue);
      return "";
    }

    // ZXing fallback (works in most browsers)
    async function ensureZXing() {
      if (window.ZXing && window.ZXing.BrowserMultiFormatReader) return window.ZXing;
      // Try to load dynamically (in case CDN script isn't loaded yet when DOMContentLoaded fires)
      const existing = document.querySelector('script[data-zxing-loader="1"]');
      if (!existing) {
        const s = document.createElement("script");
        s.src = "https://unpkg.com/@zxing/library@0.21.3/umd/index.min.js";
        s.defer = true;
        s.setAttribute("data-zxing-loader", "1");
        document.head.appendChild(s);
      }
      const start = Date.now();
      while (Date.now() - start < 4500) {
        if (window.ZXing && window.ZXing.BrowserMultiFormatReader) return window.ZXing;
        await new Promise((r) => setTimeout(r, 50));
      }
      return null;
    }

    const ZXing = await ensureZXing();
    if (!ZXing) return "";

    const reader = new ZXing.BrowserMultiFormatReader();
    const url = URL.createObjectURL(file);
    try {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.src = url;
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
      });
      const result = await reader.decodeFromImageElement(img);
      return result && result.getText ? String(result.getText()) : "";
    } catch (e) {
      return "";
    } finally {
      try {
        URL.revokeObjectURL(url);
      } catch (e) {}
    }
  }

  function init() {
    const box = qs("[data-barcode-box]");
    if (!box) return;

    const scanBtn = qs("#barcode-scan-btn", box);
    const imgBtn = qs("#barcode-image-btn", box);
    const imgInput = qs("#barcode-image-input", box);
    const manual = qs("#barcode-manual", box);
    const lookupBtn = qs("#barcode-lookup-btn", box);

    const result = qs("#barcode-result", box);
    const coverWrap = qs("#barcode-cover", box);
    const coverImg = qs("#barcode-cover-img", box);
    const codeEl = qs("#barcode-code", box);
    const titleEl = qs("#barcode-title", box);
    const authorsEl = qs("#barcode-authors", box);
    const descEl = qs("#barcode-desc", box);
    const candEl = qs("#barcode-candidates", box);
    const applyBtn = qs("#barcode-apply-btn", box);
    const addCoverBtn = qs("#barcode-add-cover-btn", box);
    const hint = qs("#barcode-hint", box);
    const boxStatus = qs("#barcode-box-status", box);
    const preview = qs("#barcode-preview", box);
    const previewImg = qs("#barcode-preview-img", box);
    const previewOpen = qs("#barcode-preview-open", box);

    const modal = qs("#barcode-modal");
    const video = qs("#barcode-video");
    const status = qs("#barcode-status");

    const itemTitle = qs('input[name="title"]');
    const itemDesc = qs('textarea[name="description"]');
    const imagesInput = qs("#id_images");

    let lastLookup = null; // {title, description, cover_url, authors}
    let stream = null;
    let scanning = false;
    let previewUrl = "";

    function setStatus(t) {
      if (status) status.textContent = t || "";
      if (boxStatus) boxStatus.textContent = t || "";
    }

    function openModal() {
      if (!modal) return;
      modal.hidden = false;
      document.body.classList.add("modal-open");
    }

    function closeModal() {
      if (!modal) return;
      modal.hidden = true;
      document.body.classList.remove("modal-open");
      if (video) video.srcObject = null;
      if (stream) {
        try {
          stream.getTracks().forEach((t) => t.stop());
        } catch (e) {}
      }
      stream = null;
      scanning = false;
    }

    function openImageModal(src) {
      if (!src) return;
      let m = document.getElementById("barcode-image-modal");
      if (!m) {
        m = document.createElement("div");
        m.id = "barcode-image-modal";
        m.className = "barcode-image-modal";
        m.hidden = true;
        m.innerHTML = `
          <div class="barcode-image-backdrop" data-close="1"></div>
          <div class="barcode-image-dialog" role="dialog" aria-modal="true">
            <button type="button" class="barcode-image-close" data-close="1" aria-label="Закрыть">✕</button>
            <img class="barcode-image-full" alt="">
          </div>
        `;
        document.body.appendChild(m);
        m.addEventListener("click", (e) => {
          const t = e.target;
          if (t && t.getAttribute && t.getAttribute("data-close") === "1") m.hidden = true;
        });
        document.addEventListener("keydown", (e) => {
          if (e.key === "Escape" && !m.hidden) m.hidden = true;
        });
      }
      const img = m.querySelector(".barcode-image-full");
      if (img) img.src = src;
      m.hidden = false;
    }

    async function renderLookup(data) {
      lastLookup = data || null;
      if (!data || !data.ok) {
        show(result, false);
        show(hint, true);
        if (candEl) {
          candEl.innerHTML = "";
          show(candEl, false);
        }
        return;
      }

      setText(codeEl, data.isbn ? `ISBN: ${data.isbn}` : `Код: ${data.code || ""}`);
      setText(titleEl, data.title || data.isbn || data.code || "");
      setText(authorsEl, (data.authors || []).join(", "));
      setText(descEl, data.description || "");

      // Candidate chooser to fix "wrong book" cases (show even if only 1, so user sees what was considered).
      if (candEl) {
        const cands = Array.isArray(data.candidates) ? data.candidates : [];
        if (cands.length >= 1) {
          const list = cands
            .map((c, idx) => {
              const t = (c && c.title) || "";
              const a = (c && c.authors && c.authors.length) ? c.authors.join(", ") : "";
              const src = (c && c.source) ? String(c.source) : "Источник";
              const badge = c && c.match ? "совпало ✓" : "похоже";
              return `
                <button type="button" class="barcode-candidate-btn" data-barcode-cand="${idx}">
                  <strong>${escapeHtml(t)}</strong>
                  <span>${escapeHtml(a)}${a ? " · " : ""}${escapeHtml(src)} · ${badge}</span>
                </button>
              `;
            })
            .join("");
          candEl.innerHTML = `
            <div class="barcode-candidates-title">Если найдено не то — выбери вариант:</div>
            <div class="barcode-candidates-list">${list}</div>
          `;
          show(candEl, true);
        } else {
          candEl.innerHTML = "";
          show(candEl, false);
        }
      }

      function setCoverWithFallback(urls) {
        if (!coverImg) return;
        const list = Array.isArray(urls) ? urls.filter(Boolean) : [];
        if (!list.length) {
          coverImg.src = "";
          show(coverWrap, false);
          show(addCoverBtn, false);
          return;
        }
        let idx = 0;
        coverImg.onload = null;
        coverImg.onerror = function () {
          idx += 1;
          if (idx >= list.length) {
            coverImg.src = "";
            show(coverWrap, false);
            show(addCoverBtn, false);
            return;
          }
          coverImg.src = list[idx];
        };
        coverImg.src = list[idx];
        show(coverWrap, true);
        show(addCoverBtn, true);
      }

      // Prefer server-provided cover_urls (best-effort), fallback to cover_url
      const coverUrls = Array.isArray(data.cover_urls) ? data.cover_urls : [];
      if (coverUrls.length) setCoverWithFallback(coverUrls);
      else if (data.cover_url) setCoverWithFallback([data.cover_url]);
      else setCoverWithFallback([]);

      show(result, true);
      show(hint, false);
    }

    function escapeHtml(s) {
      return String(s || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    function applyCandidate(data, cand) {
      if (!data || !cand) return;
      // Update "current" lookup object so Apply/Add cover uses chosen candidate.
      lastLookup = {
        ...data,
        title: cand.title || data.title,
        description: cand.description || data.description,
        authors: cand.authors || data.authors,
        cover_url: cand.cover_url || data.cover_url,
      };
      setText(titleEl, lastLookup.title || "");
      setText(authorsEl, (lastLookup.authors || []).join(", "));
      setText(descEl, lastLookup.description || "");
      // Update cover with fallbacks: chosen candidate first, then any existing fallbacks.
      const urls = [];
      if (cand.cover_url) urls.push(cand.cover_url);
      if (data && Array.isArray(data.cover_urls)) urls.push.apply(urls, data.cover_urls);
      if (lastLookup.cover_url) urls.push(lastLookup.cover_url);
      const seen = new Set();
      const dedup = urls.filter((u) => {
        if (!u || seen.has(u)) return false;
        seen.add(u);
        return true;
      });
      if (dedup.length) {
        // Reuse render fallback loader by calling renderLookup partially
        if (coverImg) {
          let i = 0;
          coverImg.onerror = function () {
            i += 1;
            if (i >= dedup.length) {
              coverImg.src = "";
              show(coverWrap, false);
              show(addCoverBtn, false);
              return;
            }
            coverImg.src = dedup[i];
          };
          coverImg.src = dedup[0];
          show(coverWrap, true);
          show(addCoverBtn, true);
        }
      } else {
        if (coverImg) coverImg.src = "";
        show(coverWrap, false);
        show(addCoverBtn, false);
      }
    }

    async function doLookup(code) {
      const cleaned = normalizeCode(code);
      if (!cleaned) return;
      if (manual) manual.value = cleaned;
      setStatus("Ищу данные…");
      try {
        const data = await fetchJson("/library/api/barcode-lookup/", { code: cleaned });
        await renderLookup(data);
        setStatus("");
      } catch (e) {
        await renderLookup(null);
        setStatus("Не удалось найти данные по коду.");
      }
    }

    if (lookupBtn) {
      lookupBtn.addEventListener("click", () => doLookup(manual ? manual.value : ""));
    }
    if (manual) {
      manual.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          doLookup(manual.value);
        }
      });
    }

    if (imgBtn && imgInput) {
      imgBtn.addEventListener("click", () => imgInput.click());
    }

    if (imgInput) {
      imgInput.addEventListener("change", async () => {
        const file = imgInput.files && imgInput.files[0];
        if (!file) return;
        if (previewImg) {
          try {
            if (previewUrl) {
              try {
                URL.revokeObjectURL(previewUrl);
              } catch (e) {}
            }
            previewUrl = URL.createObjectURL(file);
            previewImg.src = previewUrl;
            show(preview, true);
          } catch (e) {}
        }
        setStatus("Распознаю штрих‑код на фото…");
        const code = await decodeFromImageFile(file);
        if (!code) {
          setStatus("Не получилось распознать. Попробуй другое фото или камеру, либо введи код вручную.");
          return;
        }
        await doLookup(code);
      });
    }

    // Apply metadata to form
    if (applyBtn) {
      applyBtn.addEventListener("click", () => {
        if (!lastLookup) return;
        if (itemTitle && lastLookup.title) itemTitle.value = lastLookup.title;
        if (itemDesc && lastLookup.description) itemDesc.value = lastLookup.description;
      });
    }

    if (candEl) {
      candEl.addEventListener("click", (e) => {
        const btn = e.target && e.target.closest ? e.target.closest("[data-barcode-cand]") : null;
        if (!btn || !lastLookup) return;
        const idx = Number(btn.getAttribute("data-barcode-cand") || "0");
        const data = lastLookup;
        const cands = Array.isArray(data.candidates) ? data.candidates : [];
        const cand = cands[idx];
        if (cand) applyCandidate(data, cand);
      });
    }

    // Add cover image into uploads (best-effort)
    if (addCoverBtn) {
      addCoverBtn.addEventListener("click", async () => {
        if (!lastLookup || !lastLookup.cover_url || !imagesInput) return;
        try {
          const csrf = getCookie("csrftoken");
          const res = await fetch("/library/api/fetch-image/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(csrf ? { "X-CSRFToken": csrf } : {}),
            },
            body: JSON.stringify({ url: lastLookup.cover_url }),
          });
          const blob = await res.blob();
          const file = new File([blob], "cover.jpg", { type: blob.type || "image/jpeg" });

          // Append to existing input.files (if any) and trigger change.
          const dt = new DataTransfer();
          Array.from(imagesInput.files || []).forEach((f) => dt.items.add(f));
          dt.items.add(file);
          imagesInput.files = dt.files;
          imagesInput.dispatchEvent(new Event("change", { bubbles: true }));

          // After previews render, click last thumb so it becomes cover
          setTimeout(() => {
            const thumbs = document.querySelectorAll("#library-upload-previews .upload-thumb");
            const last = thumbs && thumbs.length ? thumbs[thumbs.length - 1] : null;
            if (last) last.click();
          }, 30);
        } catch (e) {
          setStatus("Не удалось добавить обложку автоматически. Можно скачать её и загрузить вручную.");
        }
      });
    }

    // Camera scan
    async function startCameraScan() {
      if (!modal || !video) return;
      openModal();
      setStatus("Запрашиваю камеру…");
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
        video.srcObject = stream;
        await video.play();
      } catch (e) {
        setStatus("Не удалось открыть камеру.");
        return;
      }

      scanning = true;
      setStatus("Наведи камеру на штрих‑код…");

      // Prefer native detector
      if ("BarcodeDetector" in window) {
        const types = ["ean_13", "ean_8", "upc_a", "code_128", "qr_code"];
        const detector = new window.BarcodeDetector({ formats: types });
        const tick = async () => {
          if (!scanning) return;
          try {
            const codes = await detector.detect(video);
            if (codes && codes[0] && codes[0].rawValue) {
              const val = String(codes[0].rawValue);
              scanning = false;
              closeModal();
              await doLookup(val);
              return;
            }
          } catch (e) {}
          requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
        return;
      }

      // ZXing fallback
      // Ensure ZXing exists
      const ZXing = window.ZXing;
      if (!ZXing || !ZXing.BrowserMultiFormatReader) {
        setStatus("Сканер не поддерживается в этом браузере. Попробуй другой браузер или ввод кода вручную.");
        return;
      }

      try {
        const reader = new ZXing.BrowserMultiFormatReader();
        const result = await reader.decodeOnceFromVideoElement(video);
        if (result && result.getText) {
          const val = String(result.getText());
          scanning = false;
          closeModal();
          await doLookup(val);
        }
      } catch (e) {
        // user closed / failed
      }
    }

    if (scanBtn) scanBtn.addEventListener("click", startCameraScan);

    if (previewOpen && previewImg) {
      previewOpen.addEventListener("click", () => {
        if (previewImg.src) openImageModal(previewImg.src);
      });
    }

    window.addEventListener("beforeunload", () => {
      if (previewUrl) {
        try {
          URL.revokeObjectURL(previewUrl);
        } catch (e) {}
      }
    });

    if (modal) {
      modal.addEventListener("click", (e) => {
        const t = e.target;
        if (!(t instanceof HTMLElement)) return;
        if (t.hasAttribute("data-barcode-close")) closeModal();
      });
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();

