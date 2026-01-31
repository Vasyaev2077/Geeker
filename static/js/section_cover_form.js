(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function initSectionCoverFormCropper() {
    const fileInput = $("id_cover");
    const modal = $("section-cover-crop-modal");
    const closeBtns = modal ? modal.querySelectorAll("[data-section-cover-close]") : [];
    const saveBtn = $("section-cover-crop-save");
    const cropImg = $("section-cover-crop-img");
    const previewImg = $("section-cover-preview-img");

    if (!fileInput || !modal || !saveBtn || !cropImg || !previewImg) return;

    let cropper = null;
    let currentObjectUrl = null;

    function openModal() {
      modal.hidden = false;
      modal.setAttribute("aria-hidden", "false");
      document.body.classList.add("modal-open");
    }

    function closeModal() {
      modal.hidden = true;
      modal.setAttribute("aria-hidden", "true");
      document.body.classList.remove("modal-open");
      if (cropper) {
        cropper.destroy();
        cropper = null;
      }
    }

    function cleanupObjectUrl() {
      if (currentObjectUrl) {
        try {
          URL.revokeObjectURL(currentObjectUrl);
        } catch (e) {}
        currentObjectUrl = null;
      }
    }

    function ensureCropper() {
      if (!window.Cropper) return null;
      cropper = new window.Cropper(cropImg, {
        aspectRatio: 1,
        viewMode: 1,
        autoCropArea: 0.98,
        dragMode: "move",
        background: false,
        movable: true,
        zoomable: true,
        zoomOnTouch: true,
        zoomOnWheel: true,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
        preview: ".section-cover-crop-preview",
      });
      return cropper;
    }

    function loadFileForCropping(file) {
      cleanupObjectUrl();
      currentObjectUrl = URL.createObjectURL(file);
      cropImg.src = currentObjectUrl;
      openModal();
      setTimeout(function () {
        if (cropper) cropper.destroy();
        cropper = ensureCropper();
      }, 0);
    }

    fileInput.addEventListener("change", function () {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      const name = (file.name || "").toLowerCase();
      const looksLikeImage =
        (file.type && file.type.startsWith("image/")) ||
        /\.(png|jpe?g|gif|webp|bmp)$/i.test(name);
      if (!looksLikeImage) return;

      // If CropperJS didn't load for some reason, fallback to plain preview.
      if (!window.Cropper) {
        const url = URL.createObjectURL(file);
        previewImg.src = url;
        previewImg.style.display = "";
        return;
      }

      loadFileForCropping(file);
    });

    closeBtns.forEach(function (btn) {
      btn.addEventListener("click", closeModal);
    });

    saveBtn.addEventListener("click", function () {
      if (!cropper) return;
      const canvas = cropper.getCroppedCanvas({
        width: 768,
        height: 768,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: "high",
      });
      if (!canvas) return;

      canvas.toBlob(
        function (blob) {
          if (!blob) return;
          const file = new File([blob], "section_cover.jpg", { type: "image/jpeg" });
          const dt = new DataTransfer();
          dt.items.add(file);
          fileInput.files = dt.files;

          const blobUrl = URL.createObjectURL(blob);
          previewImg.src = blobUrl;
          previewImg.style.display = "";

          closeModal();
        },
        "image/jpeg",
        0.92
      );
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSectionCoverFormCropper();
  });
})();

