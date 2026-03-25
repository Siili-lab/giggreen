/**
 * GigGreen — impact-score.js
 * Animated circular score gauge (canvas) + count-up number animation.
 * Loaded on worker dashboard.
 */

(function () {
  "use strict";

  const LEVEL_COLORS = {
    1: "#A8D5B5",
    2: "#2D9B5A",
    3: "#1A6B3A",
    4: "#F4A935",
    5: "#0F1F14",
  };

  // Max score for gauge display purposes (Level 5 starts at 1001)
  const GAUGE_MAX = 1200;

  function drawGauge(canvas, score, level) {
    if (!canvas) return;
    const ctx    = canvas.getContext("2d");
    const W      = canvas.width;
    const H      = canvas.height;
    const cx     = W / 2;
    const cy     = H / 2;
    const radius = (Math.min(W, H) / 2) - 12;
    const color  = LEVEL_COLORS[level] || LEVEL_COLORS[1];
    const pct    = Math.min(score / GAUGE_MAX, 1);
    const startAngle = -Math.PI / 2;            // 12 o'clock
    const fullAngle  = 2 * Math.PI;

    ctx.clearRect(0, 0, W, H);

    // Track (background arc)
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, fullAngle);
    ctx.strokeStyle = "rgba(212,232,218,0.4)";
    ctx.lineWidth   = 14;
    ctx.stroke();

    // Filled arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, startAngle, startAngle + fullAngle * pct);
    ctx.strokeStyle = color;
    ctx.lineWidth   = 14;
    ctx.lineCap     = "round";
    ctx.stroke();

    // Outer glow ring
    ctx.beginPath();
    ctx.arc(cx, cy, radius + 7, 0, fullAngle);
    ctx.strokeStyle = color + "22";
    ctx.lineWidth   = 6;
    ctx.stroke();
  }

  function animateGauge(canvas, targetScore, level, duration = 1200) {
    if (!canvas) return;
    const start = performance.now();
    const display = document.getElementById("scoreDisplay");

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(targetScore * eased);

      drawGauge(canvas, current, level);
      if (display) display.textContent = current.toLocaleString();

      if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
  }

  function initGauge() {
    const canvas = document.getElementById("scoreGauge");
    if (!canvas) return;
    const score = parseInt(canvas.dataset.score || "0", 10);
    const level = parseInt(canvas.dataset.level || "1", 10);
    // Small delay so the page paint completes first
    setTimeout(() => animateGauge(canvas, score, level), 300);
  }

  // ── Count-up for any element with data-countup ────────────────────────────
  function initCountUps() {
    document.querySelectorAll("[data-countup]").forEach(el => {
      const target   = parseInt(el.dataset.countup || el.textContent, 10);
      const duration = parseInt(el.dataset.duration || "800", 10);
      const start    = performance.now();

      function step(now) {
        const elapsed  = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased    = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(target * eased).toLocaleString();
        if (progress < 1) requestAnimationFrame(step);
      }

      requestAnimationFrame(step);
    });
  }

  // ── Progress bar fill animation ───────────────────────────────────────────
  function initProgressBars() {
    document.querySelectorAll(".progress-bar-fill").forEach(bar => {
      const targetWidth = bar.style.width;
      bar.style.width   = "0%";
      requestAnimationFrame(() => {
        bar.style.transition = "width 1s cubic-bezier(0.4, 0, 0.2, 1)";
        bar.style.width      = targetWidth;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initGauge();
    initCountUps();
    initProgressBars();
  });
})();
