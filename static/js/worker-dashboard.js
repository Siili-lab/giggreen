/**
 * GigGreen — worker-dashboard.js
 * Handles the Apply modal and quick-apply from dashboard gig cards.
 */

(function () {
  "use strict";

  const modal       = document.getElementById("applyModal");
  const modalTitle  = document.getElementById("modalGigTitle");
  const modalCancel = document.getElementById("modalCancel");
  const modalConfirm = document.getElementById("modalConfirm");

  let pendingGigId    = null;
  let pendingGigTitle = null;

  // ── Open modal ─────────────────────────────────────────────────────────────
  function openApplyModal(gigId, gigTitle) {
    pendingGigId    = gigId;
    pendingGigTitle = gigTitle;
    if (modalTitle) modalTitle.textContent = gigTitle;
    if (modal) {
      modal.hidden = false;
      modal.classList.add("is-open");
    }
  }

  // ── Close modal ────────────────────────────────────────────────────────────
  function closeModal() {
    if (modal) {
      modal.hidden = true;
      modal.classList.remove("is-open");
    }
    pendingGigId    = null;
    pendingGigTitle = null;
  }

  // ── Submit application ─────────────────────────────────────────────────────
  async function submitApplication() {
    if (!pendingGigId) return;

    const btn = modalConfirm;
    btn.textContent = "Applying…";
    btn.disabled    = true;

    try {
      const res  = await fetch(`/gigs/${pendingGigId}/apply`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();

      closeModal();

      if (res.ok) {
        window.GigGreen?.toast(data.message || "Applied successfully!", "success");
        // Mark button as applied on the card
        const applyBtn = document.querySelector(
          `.apply-btn[data-gig-id="${pendingGigId}"]`
        );
        if (applyBtn) {
          applyBtn.textContent = "Applied ✓";
          applyBtn.disabled    = true;
          applyBtn.classList.remove("btn-primary");
          applyBtn.classList.add("btn-applied");
        }
      } else {
        window.GigGreen?.toast(data.message || "Something went wrong.", "error");
      }
    } catch {
      closeModal();
      window.GigGreen?.toast("Connection error. Please try again.", "error");
    } finally {
      btn.textContent = "Yes, Apply!";
      btn.disabled    = false;
    }
  }

  // ── Event listeners ────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    // Apply buttons on gig cards
    document.querySelectorAll(".apply-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const gigId    = btn.dataset.gigId;
        const gigTitle = btn.dataset.gigTitle;
        openApplyModal(gigId, gigTitle);
      });
    });

    // Modal cancel
    if (modalCancel) modalCancel.addEventListener("click", closeModal);

    // Modal confirm
    if (modalConfirm) modalConfirm.addEventListener("click", submitApplication);

    // Close on overlay click
    if (modal) {
      modal.addEventListener("click", e => {
        if (e.target === modal) closeModal();
      });
    }

    // Close on Escape
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") closeModal();
    });
  });
})();
