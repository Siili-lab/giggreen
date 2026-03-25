/* ─────────────────────────────────────────────────────────────────────────────
   GigGreen — auth.js
   Login flow + Register multi-step flow, OTP input, resend timer
   ───────────────────────────────────────────────────────────────────────────── */

"use strict";

/* ═══════════════════════════════════════════════════════════════════════════
   LOGIN FLOW
   ═══════════════════════════════════════════════════════════════════════════ */
window.initLoginFlow = function () {
  const phoneInput   = document.getElementById("phone-input");
  const btnSendOtp   = document.getElementById("btn-send-otp");
  const stepPhone    = document.getElementById("step-phone");
  const stepOtp      = document.getElementById("step-otp");
  const otpDisplay   = document.getElementById("otp-phone-display");
  const btnVerify    = document.getElementById("btn-verify-otp");
  const btnBack      = document.getElementById("btn-back-phone");
  const btnResend    = document.getElementById("btn-resend");
  const resendTimer  = document.getElementById("resend-timer");
  const phoneErr     = document.getElementById("phone-error");
  const phoneErrMsg  = document.getElementById("phone-error-msg");
  const otpErr       = document.getElementById("otp-error");
  const otpErrMsg    = document.getElementById("otp-error-msg");

  let currentPhone = "";
  let resendInterval = null;

  initOtpInputs("#step-otp");

  // Enter key on phone input
  phoneInput && phoneInput.addEventListener("keydown", e => {
    if (e.key === "Enter") btnSendOtp.click();
  });

  // Send OTP
  btnSendOtp && btnSendOtp.addEventListener("click", async () => {
    phoneErr.style.display = "none";
    const raw = phoneInput.value.trim();
    const phone = normalisePhone(raw);

    if (!validatePhone(phone)) {
      showFieldError(phoneErr, phoneErrMsg, "Please enter a valid Kenyan phone number (e.g. 0712345678).");
      return;
    }

    currentPhone = phone;
    btnSendOtp.classList.add("is-loading");
    btnSendOtp.textContent = "Sending…";

    const res = await apiFetch("/auth/send-otp", {
      method: "POST",
      body: JSON.stringify({ phone }),
    });

    btnSendOtp.classList.remove("is-loading");
    btnSendOtp.innerHTML = `<i data-lucide="message-square" width="18" height="18"></i> Send verification code`;
    if (window.lucide) lucide.createIcons();

    if (res.ok) {
      otpDisplay.textContent = formatPhoneDisplay(phone);
      stepPhone.style.display = "none";
      stepOtp.style.display = "block";
      document.querySelector("#step-otp .otp-input").focus();
      startResendTimer(btnResend, resendTimer, 60);
    } else {
      showFieldError(phoneErr, phoneErrMsg, res.data.message || "Could not send OTP. Try again.");
    }
  });

  // Back to phone
  btnBack && btnBack.addEventListener("click", () => {
    stepOtp.style.display = "none";
    stepPhone.style.display = "block";
    clearInterval(resendInterval);
  });

  // Verify OTP
  btnVerify && btnVerify.addEventListener("click", async () => {
    otpErr.style.display = "none";
    const code = getOtpValue("#step-otp");

    if (code.length !== 6) {
      showFieldError(otpErr, otpErrMsg, "Please enter all 6 digits.");
      return;
    }

    btnVerify.classList.add("is-loading");

    const res = await apiFetch("/auth/verify-otp", {
      method: "POST",
      body: JSON.stringify({ phone: currentPhone, code }),
    });

    btnVerify.classList.remove("is-loading");

    if (res.ok) {
      showToast("Signed in! Welcome back.", "success");
      window.location.href = res.data.redirect || "/worker/dashboard";
    } else {
      showFieldError(otpErr, otpErrMsg, res.data.message || "Incorrect code. Please try again.");
    }
  });

  // Resend
  btnResend && btnResend.addEventListener("click", async () => {
    const res = await apiFetch("/auth/send-otp", {
      method: "POST",
      body: JSON.stringify({ phone: currentPhone }),
    });
    if (res.ok) {
      showToast("New code sent!", "success");
      startResendTimer(btnResend, resendTimer, 60);
    } else {
      showToast("Could not resend. Try again.", "error");
    }
  });
};

/* ═══════════════════════════════════════════════════════════════════════════
   REGISTER FLOW
   ═══════════════════════════════════════════════════════════════════════════ */
window.initRegisterFlow = function () {
  let currentStep  = 1;
  let currentPhone = "";
  let userType     = "worker";

  const state = {
    phone: "", user_type: "worker", name: "", location: "",
    company_name: "", sector: "", availability: "full-time",
    bio: "", green_categories: "[]",
  };

  autoSaveForm(document.querySelector(".auth-form-wrap"), "reg_form");
  initOtpInputs("#reg-otp-inputs");

  // ── Collect user_type radio ──
  document.querySelectorAll('input[name="user_type"]').forEach(r => {
    r.addEventListener("change", () => { userType = r.value; state.user_type = r.value; });
  });

  // ── STEP 1: Send OTP ──
  document.getElementById("reg-btn-send-otp").addEventListener("click", async () => {
    const raw   = document.getElementById("reg-phone").value.trim();
    const phone = normalisePhone(raw);
    const errEl = document.getElementById("reg-phone-error");
    const msgEl = document.getElementById("reg-phone-error-msg");
    errEl.style.display = "none";

    if (!validatePhone(phone)) {
      showFieldError(errEl, msgEl, "Enter a valid Kenyan number — e.g. 0712345678");
      return;
    }

    currentPhone  = phone;
    state.phone   = phone;

    const btn = document.getElementById("reg-btn-send-otp");
    btn.classList.add("is-loading");

    const res = await apiFetch("/auth/send-otp", {
      method: "POST",
      body: JSON.stringify({ phone, is_register: true }),
    });

    btn.classList.remove("is-loading");

    if (res.ok) {
      document.getElementById("reg-phone-display").textContent = formatPhoneDisplay(phone);
      goToStep(2);
      document.querySelector("#reg-otp-inputs .otp-input").focus();
      startResendTimer(
        document.getElementById("reg-btn-resend"),
        null, 60
      );
    } else {
      showFieldError(errEl, msgEl, res.data.message || "Could not send code. Try again.");
    }
  });

  // ── STEP 2 back ──
  document.getElementById("reg-btn-back-1").addEventListener("click", () => goToStep(1));

  // ── STEP 2: Verify OTP ──
  document.getElementById("reg-btn-verify-otp").addEventListener("click", async () => {
    const code  = getOtpValue("#reg-otp-inputs");
    const errEl = document.getElementById("reg-otp-error");
    const msgEl = document.getElementById("reg-otp-error-msg");
    errEl.style.display = "none";

    if (code.length !== 6) {
      showFieldError(errEl, msgEl, "Enter all 6 digits.");
      return;
    }

    const btn = document.getElementById("reg-btn-verify-otp");
    btn.classList.add("is-loading");

    const res = await apiFetch("/auth/verify-otp", {
      method: "POST",
      body: JSON.stringify({ phone: currentPhone, code, is_register: true }),
    });

    btn.classList.remove("is-loading");

    if (res.ok) {
      markCheck("check-verify");
      goToStep(3);
    } else {
      showFieldError(errEl, msgEl, res.data.message || "Incorrect code. Try again.");
    }
  });

  // ── STEP 3: Profile ──
  document.getElementById("reg-btn-next-3").addEventListener("click", () => {
    const name   = document.getElementById("reg-name").value.trim();
    const county = document.getElementById("reg-county").value;

    if (!name) { showToast("Please enter your name.", "warning"); return; }
    if (!county) { showToast("Please select your county.", "warning"); return; }

    state.name     = name;
    state.location = county;
    state.bio      = document.getElementById("reg-bio").value.trim();
    state.availability = document.querySelector('input[name="availability"]:checked')?.value || "full-time";

    if (userType === "employer") {
      state.company_name = document.getElementById("reg-company").value.trim();
      state.sector       = document.getElementById("reg-sector").value;
      if (!state.company_name) { showToast("Please enter your company name.", "warning"); return; }
    }

    markCheck("check-profile");
    goToStep(4);
  });

  // ── STEP 4: Submit ──
  document.getElementById("reg-btn-submit").addEventListener("click", async () => {
    state.green_categories = document.getElementById("reg-categories").value;

    const btn = document.getElementById("reg-btn-submit");
    btn.classList.add("is-loading");
    btn.disabled = true;

    const res = await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify(state),
    });

    btn.classList.remove("is-loading");

    if (res.ok) {
      markCheck("check-skills");
      clearFormSave("reg_form");
      goToStep("success");
      if (res.data.redirect_employer) {
        document.getElementById("reg-go-dashboard").href = res.data.redirect_employer;
      }
    } else {
      btn.disabled = false;
      showToast(res.data.message || "Something went wrong. Please try again.", "error");
    }
  });

  // ── Resend ──
  document.getElementById("reg-btn-resend").addEventListener("click", async () => {
    const res = await apiFetch("/auth/send-otp", {
      method: "POST",
      body: JSON.stringify({ phone: currentPhone, is_register: true }),
    });
    if (res.ok) showToast("New code sent!", "success");
    else showToast("Could not resend.", "error");
  });

  /* helpers */
  function goToStep(n) {
    currentStep = n;
    document.querySelectorAll(".form-step").forEach(s => { s.style.display = "none"; s.classList.remove("active"); });
    const target = n === "success"
      ? document.getElementById("reg-step-success")
      : document.getElementById(`reg-step-${n}`);
    if (target) { target.style.display = "block"; target.classList.add("active"); }

    // Update progress dots
    document.querySelectorAll(".progress-step").forEach(ps => {
      const step = parseInt(ps.dataset.step);
      ps.classList.remove("active", "done");
      if (typeof n === "number") {
        if (step < n)  ps.classList.add("done");
        if (step === n) ps.classList.add("active");
      } else {
        ps.classList.add("done");
      }
    });

    // Mark panel checks
    if (n >= 2) markCheck("check-phone");
    if (n >= 3) markCheck("check-verify");
    if (n >= 4) markCheck("check-profile");
    if (n === "success") markCheck("check-skills");

    window.scrollTo({ top: 0, behavior: "smooth" });
    if (window.lucide) lucide.createIcons();
  }

  function markCheck(id) {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add("done");
      el.querySelector("i")?.setAttribute("data-lucide", "check-circle-2");
      if (window.lucide) lucide.createIcons();
    }
  }
};

/* ═══════════════════════════════════════════════════════════════════════════
   SHARED HELPERS
   ═══════════════════════════════════════════════════════════════════════════ */

function getOtpValue(containerSelector) {
  const inputs = document.querySelectorAll(`${containerSelector} .otp-input`);
  return Array.from(inputs).map(i => i.value).join("").trim();
}

function validatePhone(phone) {
  return /^\+2547\d{8}$/.test(phone);
}

function showFieldError(errEl, msgEl, msg) {
  msgEl.textContent = msg;
  errEl.style.display = "flex";
}

let resendCountdown = null;
function startResendTimer(btnEl, timerEl, seconds) {
  if (!btnEl) return;
  btnEl.disabled = true;
  btnEl.style.opacity = "0.5";

  let remaining = seconds;
  if (timerEl) timerEl.style.display = "inline";

  const tick = () => {
    if (timerEl) timerEl.textContent = ` (${remaining}s)`;
    if (remaining <= 0) {
      clearInterval(resendCountdown);
      btnEl.disabled = false;
      btnEl.style.opacity = "1";
      if (timerEl) timerEl.style.display = "none";
    }
    remaining--;
  };

  tick();
  resendCountdown = setInterval(tick, 1000);
}
