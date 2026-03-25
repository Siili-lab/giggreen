/**
 * GigGreen — gig-feed.js
 * Handles apply modal + confirmation flow on the gig feed page.
 */

(function () {
  "use strict";

  const modal        = document.getElementById("applyModal");
  const modalTitle   = document.getElementById("modalGigTitle");
  const modalPay     = document.getElementById("modalGigPay");
  const modalPts     = document.getElementById("modalGigPts");
  const modalCancel  = document.getElementById("modalCancel");
  const modalConfirm = document.getElementById("modalConfirm");

  let pendingGigId = null;

  function openModal(gigId, gigTitle, gigPay, gigPts) {
    pendingGigId = gigId;
    if (modalTitle) modalTitle.textContent = gigTitle;
    if (modalPay)   modalPay.textContent   = `💰 KES ${Number(gigPay).toLocaleString()}`;
    if (modalPts)   modalPts.textContent   = `⭐ +${gigPts} impact points`;
    if (modal) {
      modal.hidden = false;
      modal.classList.add("is-open");
    }
  }

  function closeModal() {
    pendingGigId = null;
    if (modal) {
      modal.hidden = true;
      modal.classList.remove("is-open");
    }
  }

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
        window.GigGreen?.toast(data.message || "Applied!", "success");

        // Replace apply button with applied state
        const card   = document.querySelector(`.gig-card[data-gig-id="${pendingGigId}"]`);
        const applyBtn = card?.querySelector(".apply-btn");
        if (applyBtn) {
          applyBtn.outerHTML = `<span class="btn btn-applied">Applied ✓</span>`;
        }
        if (card) card.classList.add("gig-applied");
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

  // ── Client-side category filter (instant, no page reload) ─────────────────
  function initClientFilter() {
    const chips = document.querySelectorAll(".filter-chip");
    chips.forEach(chip => {
      chip.addEventListener("click", () => {
        const cat = chip.dataset.category || "";
        chips.forEach(c => c.classList.remove("active"));
        chip.classList.add("active");

        document.querySelectorAll(".gig-card").forEach(card => {
          const cardCat = card.dataset.category || "";
          card.style.display = (!cat || cardCat === cat) ? "" : "none";
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    // Wire apply buttons
    document.querySelectorAll(".apply-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        openModal(
          btn.dataset.gigId,
          btn.dataset.gigTitle,
          btn.dataset.gigPay,
          btn.dataset.gigPts,
        );
      });
    });

    if (modalCancel)  modalCancel.addEventListener("click", closeModal);
    if (modalConfirm) modalConfirm.addEventListener("click", submitApplication);
    if (modal) modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });
    document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

    initClientFilter();
  });
})();
