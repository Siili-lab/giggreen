/**
 * GigGreen — Employer Dashboard JS
 * Handles: confirm worker, release payment, live stat updates
 */

document.addEventListener("DOMContentLoaded", () => {
  initConfirmWorker();
  initReleasePayment();
  initStatAnimations();
});

/* ─── Confirm Worker ─────────────────────────────────────── */
function initConfirmWorker() {
  document.querySelectorAll("[data-confirm-worker]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const gigId    = btn.dataset.gigId;
      const workerId = btn.dataset.workerId;

      if (!confirm("Confirm this worker for the gig?")) return;

      btn.disabled    = true;
      btn.textContent = "Confirming…";

      try {
        const res  = await apiFetch("/employer/api/confirm-worker", {
          method: "POST",
          body: JSON.stringify({ gig_id: gigId, worker_id: workerId }),
        });

        if (res.ok) {
          showToast("Worker confirmed! They'll be notified by SMS.", "success");
          // Refresh the card status badge
          const card = btn.closest(".gig-card");
          if (card) {
            const badge = card.querySelector(".gig-status");
            if (badge) {
              badge.textContent = "In Progress";
              badge.className   = "gig-status gig-status--in_progress";
            }
          }
          btn.textContent = "✅ Confirmed";
        } else {
          const data = await res.json().catch(() => ({}));
          showToast(data.error || "Could not confirm worker.", "error");
          btn.disabled    = false;
          btn.textContent = "Confirm";
        }
      } catch (err) {
        showToast("Network error — please try again.", "error");
        btn.disabled    = false;
        btn.textContent = "Confirm";
      }
    });
  });
}

/* ─── Release Payment ────────────────────────────────────── */
function initReleasePayment() {
  document.querySelectorAll("[data-release-payment]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const gigId = btn.dataset.gigId;

      if (!confirm("Release payment to the worker via M-Pesa?")) return;

      btn.disabled    = true;
      btn.textContent = "Releasing…";

      try {
        const res = await apiFetch("/payments/release", {
          method: "POST",
          body: JSON.stringify({ gig_id: gigId }),
        });

        if (res.ok) {
          showToast("Payment released! Worker will receive M-Pesa shortly.", "success");
          const card = btn.closest(".gig-card");
          if (card) {
            const badge = card.querySelector(".gig-status");
            if (badge) {
              badge.textContent = "Completed";
              badge.className   = "gig-status gig-status--completed";
            }
          }
          btn.textContent = "✅ Paid";
        } else {
          const data = await res.json().catch(() => ({}));
          showToast(data.error || "Payment failed.", "error");
          btn.disabled    = false;
          btn.textContent = "Release Payment";
        }
      } catch (err) {
        showToast("Network error — please try again.", "error");
        btn.disabled    = false;
        btn.textContent = "Release Payment";
      }
    });
  });
}

/* ─── Stat card count-up animation ──────────────────────── */
function initStatAnimations() {
  document.querySelectorAll(".stat-number").forEach((el) => {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target) || target === 0) return;

    let current  = 0;
    const step   = Math.ceil(target / 30);
    const timer  = setInterval(() => {
      current += step;
      if (current >= target) {
        el.textContent = target;
        clearInterval(timer);
      } else {
        el.textContent = current;
      }
    }, 30);
  });
}

/* ─── Shared fetch helper ────────────────────────────────── */
async function apiFetch(url, options = {}) {
  const defaults = {
    headers: { "Content-Type": "application/json" },
  };
  return fetch(url, { ...defaults, ...options });
}

/* ─── Toast (fallback if main.js not loaded) ─────────────── */
function showToast(message, type = "info") {
  // Use global showToast from main.js if available
  if (window.GigGreen && window.GigGreen.toast) {
    window.GigGreen.toast(message, type);
    return;
  }
  // Fallback
  const toast       = document.createElement("div");
  toast.className   = `toast toast--${type}`;
  toast.textContent = message;
  Object.assign(toast.style, {
    position:     "fixed",
    bottom:       "1.5rem",
    right:        "1.5rem",
    padding:      "0.75rem 1.25rem",
    borderRadius: "0.5rem",
    background:   type === "success" ? "#22c55e" : type === "error" ? "#ef4444" : "#3b82f6",
    color:        "#fff",
    zIndex:       9999,
    fontSize:     "0.9rem",
    boxShadow:    "0 4px 12px rgba(0,0,0,0.15)",
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}