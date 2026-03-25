/* ─────────────────────────────────────────────────────────────────────────────
   GigGreen — main.js
   Global utilities: fetch wrapper, toast, offline detection, reveal observer,
   mobile nav, phone formatter, localStorage helpers
   ───────────────────────────────────────────────────────────────────────────── */

"use strict";

/* ── Toast ─────────────────────────────────────────────────────────────────── */
const TOAST_ICONS = {
  success: `<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  error:   `<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  warning: `<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  info:    `<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
};

/**
 * Show a toast notification.
 * @param {string} message
 * @param {'success'|'error'|'warning'|'info'} type
 * @param {number} duration  ms
 */
window.showToast = function (message, type = "info", duration = 4000) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `${TOAST_ICONS[type] || ""}<span>${message}</span>`;
  container.appendChild(toast);

  const remove = () => {
    toast.classList.add("is-removing");
    toast.addEventListener("animationend", () => toast.remove(), { once: true });
  };

  const timer = setTimeout(remove, duration);
  toast.addEventListener("click", () => { clearTimeout(timer); remove(); });
};

/* ── Fetch wrapper ─────────────────────────────────────────────────────────── */
/**
 * Fetch with JSON convenience and error handling.
 * @param {string} url
 * @param {object} options  standard fetch options
 * @returns {Promise<{ok: boolean, data: any, status: number}>}
 */
window.apiFetch = async function (url, options = {}) {
  try {
    const defaults = {
      headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
    };
    const merged = { ...defaults, ...options };
    if (merged.headers && options.headers) {
      merged.headers = { ...defaults.headers, ...options.headers };
    }

    const res = await fetch(url, merged);
    let data = null;
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      data = await res.json();
    } else {
      data = { message: await res.text() };
    }
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    console.error("[apiFetch] Network error:", err);
    return { ok: false, status: 0, data: { message: "Network error. Check your connection." } };
  }
};

/* ── Phone number normaliser ───────────────────────────────────────────────── */
/**
 * Normalise Kenyan phone numbers to +2547XXXXXXXX format.
 * Accepts: 07xx, 2547xx, +2547xx
 */
window.normalisePhone = function (raw) {
  const digits = raw.replace(/\D/g, "");
  if (digits.startsWith("2547") && digits.length === 12) return `+${digits}`;
  if (digits.startsWith("07") && digits.length === 10) return `+254${digits.slice(1)}`;
  if (digits.startsWith("7") && digits.length === 9)   return `+254${digits}`;
  return raw; // return as-is if unrecognised
};

/**
 * Format a phone for display: +254712345678 → 0712 345 678
 */
window.formatPhoneDisplay = function (phone) {
  const d = phone.replace(/\D/g, "");
  if (d.startsWith("254") && d.length === 12) {
    const local = "0" + d.slice(3);
    return `${local.slice(0,4)} ${local.slice(4,7)} ${local.slice(7)}`;
  }
  return phone;
};

/* ── Form auto-save to localStorage ───────────────────────────────────────── */
window.autoSaveForm = function (formEl, storageKey) {
  if (!formEl) return;
  const inputs = formEl.querySelectorAll("input, textarea, select");

  // Restore saved values
  const saved = window.getLocalData(storageKey);
  if (saved) {
    inputs.forEach(input => {
      if (input.name && saved[input.name] !== undefined) {
        input.value = saved[input.name];
      }
    });
  }

  // Save on every change
  inputs.forEach(input => {
    input.addEventListener("input", () => {
      const data = {};
      inputs.forEach(i => { if (i.name) data[i.name] = i.value; });
      window.setLocalData(storageKey, data);
    });
  });
};

window.clearFormSave = function (storageKey) {
  try { localStorage.removeItem(storageKey); } catch (_) {}
};

/* ── localStorage helpers ──────────────────────────────────────────────────── */
window.setLocalData = function (key, value) {
  try { localStorage.setItem(`gg_${key}`, JSON.stringify(value)); } catch (_) {}
};

window.getLocalData = function (key) {
  try {
    const raw = localStorage.getItem(`gg_${key}`);
    return raw ? JSON.parse(raw) : null;
  } catch (_) { return null; }
};

window.clearLocalData = function (key) {
  try { localStorage.removeItem(`gg_${key}`); } catch (_) {}
};

/* ── Offline detection banner ──────────────────────────────────────────────── */
(function initOfflineBanner() {
  const banner = document.getElementById("offline-banner") || (() => {
    const el = document.createElement("div");
    el.id = "offline-banner";
    el.className = "offline-banner";
    el.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
        <line x1="1" y1="1" x2="23" y2="23"/>
        <path d="M16.72 11.06A10.94 10.94 0 0119 12.55"/>
        <path d="M5 12.55a10.94 10.94 0 015.17-2.39"/>
        <path d="M10.71 5.05A16 16 0 0122.56 9"/>
        <path d="M1.42 9a15.91 15.91 0 014.7-2.88"/>
        <path d="M8.53 16.11a6 6 0 016.95 0"/>
        <line x1="12" y1="20" x2="12.01" y2="20"/>
      </svg>
      You're offline — your progress is saved locally.
    `;
    document.body.appendChild(el);
    return el;
  })();

  const update = () => {
    banner.classList.toggle("is-visible", !navigator.onLine);
    if (!navigator.onLine) {
      showToast("You're offline. Don't worry — your work is saved.", "warning", 6000);
    }
  };

  window.addEventListener("online",  update);
  window.addEventListener("offline", update);
  update();
})();

/* ── Scroll-triggered reveal ───────────────────────────────────────────────── */
(function initReveal() {
  const els = document.querySelectorAll(".reveal");
  if (!els.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  els.forEach(el => observer.observe(el));
})();

/* ── Mobile nav toggle ─────────────────────────────────────────────────────── */
(function initMobileNav() {
  const hamburger = document.querySelector(".nav__hamburger");
  const mobileMenu = document.querySelector(".nav__mobile");
  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener("click", () => {
    const isOpen = mobileMenu.classList.toggle("is-open");
    hamburger.setAttribute("aria-expanded", isOpen);
  });

  // Close on outside click
  document.addEventListener("click", (e) => {
    if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
      mobileMenu.classList.remove("is-open");
    }
  });
})();

/* ── OTP input keyboard navigation ────────────────────────────────────────── */
window.initOtpInputs = function (containerSelector) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  const inputs = container.querySelectorAll(".otp-input");

  inputs.forEach((input, i) => {
    input.addEventListener("input", (e) => {
      const val = e.target.value.replace(/\D/g, "");
      e.target.value = val.slice(-1);
      if (val && i < inputs.length - 1) inputs[i + 1].focus();
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !input.value && i > 0) {
        inputs[i - 1].focus();
      }
    });

    input.addEventListener("paste", (e) => {
      e.preventDefault();
      const pasted = (e.clipboardData || window.clipboardData).getData("text").replace(/\D/g, "");
      inputs.forEach((inp, j) => { inp.value = pasted[j] || ""; });
      const lastFilled = Math.min(pasted.length, inputs.length) - 1;
      if (lastFilled >= 0) inputs[lastFilled].focus();
    });
  });
};

/* ── Score count-up animation ─────────────────────────────────────────────── */
window.animateScore = function (el, targetValue, duration = 1200) {
  if (!el) return;
  const start = performance.now();
  const from  = 0;

  const tick = (now) => {
    const elapsed  = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
    el.textContent = Math.round(from + (targetValue - from) * eased);
    if (progress < 1) requestAnimationFrame(tick);
  };

  requestAnimationFrame(tick);
};

/* ── Score gauge SVG setup ─────────────────────────────────────────────────── */
window.initScoreGauge = function (gaugeEl, score, maxScore = 1000) {
  if (!gaugeEl) return;
  const fill    = gaugeEl.querySelector(".score-gauge__fill");
  const numEl   = gaugeEl.querySelector(".score-gauge__value");
  if (!fill || !numEl) return;

  const r           = 54;  // radius (must match SVG cx/cy/r)
  const circumference = 2 * Math.PI * r;
  const pct         = Math.min(score / maxScore, 1);
  const offset      = circumference * (1 - pct);

  fill.style.strokeDasharray  = circumference;
  fill.style.strokeDashoffset = circumference; // start at 0

  // Trigger animation after paint
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      fill.style.strokeDashoffset = offset;
    });
  });

  // Count up the number
  window.animateScore(numEl, score);
};

/* ── Progress bar animation ────────────────────────────────────────────────── */
window.animateProgressBars = function () {
  document.querySelectorAll(".progress-bar-fill[data-width]").forEach(bar => {
    const target = bar.getAttribute("data-width");
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { bar.style.width = target; });
    });
  });
  document.querySelectorAll(".impact-bar-row__fill[data-width]").forEach(bar => {
    const target = bar.getAttribute("data-width");
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { bar.style.width = target; });
    });
  });
};

// Auto-trigger progress bars on page load
document.addEventListener("DOMContentLoaded", () => {
  window.animateProgressBars();
});

/* ── Confirm apply modal helper ────────────────────────────────────────────── */
window.openModal = function (id) {
  const overlay = document.getElementById(id);
  if (overlay) overlay.classList.add("is-open");
};

window.closeModal = function (id) {
  const overlay = document.getElementById(id);
  if (overlay) overlay.classList.remove("is-open");
};

// Close modal on overlay background click
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("is-open");
  }
});

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-overlay.is-open").forEach(m => m.classList.remove("is-open"));
  }
});

/* ── Chip multi-select ─────────────────────────────────────────────────────── */
window.initChips = function (containerSelector, hiddenInputSelector) {
  const container    = document.querySelector(containerSelector);
  const hiddenInput  = document.querySelector(hiddenInputSelector);
  if (!container || !hiddenInput) return;

  const getSelected = () =>
    Array.from(container.querySelectorAll(".chip.selected")).map(c => c.dataset.value);

  container.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      chip.classList.toggle("selected");
      hiddenInput.value = JSON.stringify(getSelected());
    });
  });
};

/* ── County dropdown initialise ────────────────────────────────────────────── */
window.populateCountyDropdown = function (selectSelector) {
  const sel = document.querySelector(selectSelector);
  if (!sel) return;

  const counties = [
    "Baringo","Bomet","Bungoma","Busia","Elgeyo-Marakwet","Embu","Garissa",
    "Homa Bay","Isiolo","Kajiado","Kakamega","Kericho","Kiambu","Kilifi",
    "Kirinyaga","Kisii","Kisumu","Kitui","Kwale","Laikipia","Lamu","Machakos",
    "Makueni","Mandera","Marsabit","Meru","Migori","Mombasa","Murang'a",
    "Nairobi","Nakuru","Nandi","Narok","Nyamira","Nyandarua","Nyeri",
    "Samburu","Siaya","Taita-Taveta","Tana River","Tharaka-Nithi","Trans Nzoia",
    "Turkana","Uasin Gishu","Vihiga","Wajir","West Pokot",
  ];

  sel.innerHTML = `<option value="">Select your county</option>`;
  counties.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
  });
};

console.log("%c🌿 GigGreen loaded", "color:#1A6B3A;font-weight:700;font-size:14px;");
