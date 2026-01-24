(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function initAvatarEditor() {
    const fileInput = $("id_avatar");
    const editBtn = $("avatar-edit-btn");
    const modal = $("avatar-crop-modal");
    const closeBtns = modal ? modal.querySelectorAll("[data-avatar-close]") : [];
    const saveBtn = $("avatar-crop-save");
    const zoom = $("avatar-crop-zoom");
    const cropImg = $("avatar-crop-img");
    const previewImg = $("avatar-preview-img");
    const previewInitial = $("avatar-preview-initial");

    if (!fileInput || !editBtn || !modal || !saveBtn || !cropImg) return;

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
        autoCropArea: 0.9,
        dragMode: "move",
        background: false,
        movable: true,
        zoomable: true,
        zoomOnTouch: true,
        zoomOnWheel: true,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
        preview: ".avatar-crop-preview",
        ready: function () {},
      });
      return cropper;
    }

    function loadFileForCropping(file) {
      cleanupObjectUrl();
      currentObjectUrl = URL.createObjectURL(file);
      cropImg.src = currentObjectUrl;
      openModal();

      // Cropper needs image in DOM with src set before init
      setTimeout(function () {
        if (cropper) cropper.destroy();
        cropper = ensureCropper();
      }, 0);
    }

    editBtn.addEventListener("click", function () {
      fileInput.click();
    });

    fileInput.addEventListener("change", function () {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      if (!file.type || !file.type.startsWith("image/")) return;
      loadFileForCropping(file);
    });

    closeBtns.forEach(function (btn) {
      btn.addEventListener("click", closeModal);
    });

    // No zoom slider UI: zoom is available via mouse wheel / touch pinch (CropperJS defaults).

    saveBtn.addEventListener("click", function () {
      if (!cropper) return;
      const canvas = cropper.getCroppedCanvas({
        width: 512,
        height: 512,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: "high",
      });
      if (!canvas) return;

      canvas.toBlob(
        function (blob) {
          if (!blob) return;
          const file = new File([blob], "avatar.jpg", { type: "image/jpeg" });
          const dt = new DataTransfer();
          dt.items.add(file);
          fileInput.files = dt.files;

          const blobUrl = URL.createObjectURL(blob);
          if (previewImg) {
            previewImg.src = blobUrl;
            previewImg.style.display = "";
          }
          if (previewInitial) {
            previewInitial.style.display = "none";
          }
          closeModal();
        },
        "image/jpeg",
        0.92
      );
    });
  }

  function initBioCounter() {
    const bio = document.getElementById("id_bio");
    const counter = document.getElementById("bio-counter");
    if (!bio || !counter) return;

    const max = parseInt(bio.getAttribute("maxlength") || "200", 10) || 200;

    function render() {
      const remaining = Math.max(0, max - (bio.value || "").length);
      counter.textContent = String(remaining);
    }

    bio.addEventListener("input", render);
    render();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initAvatarEditor();
    initBioCounter();
  });
})();

