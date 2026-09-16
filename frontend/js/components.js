/**
 * StudyGen AI - UI Components & Utility Helpers
 */

// Toast Notifications
const Toast = {
  container: null,

  init() {
    this.container = document.getElementById("toastContainer");
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.id = "toastContainer";
      this.container.className = "toast-container";
      document.body.appendChild(this.container);
    }
  },

  show(message, type = "info", duration = 3500) {
    this.init();
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    const iconMap = {
      success: "✓",
      danger: "✕",
      warning: "⚠",
      info: "ℹ"
    };

    toast.innerHTML = `
      <span style="font-weight: bold;">${iconMap[type] || "•"}</span>
      <span style="flex: 1;">${message}</span>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "all 0.25s ease";
      setTimeout(() => toast.remove(), 250);
    }, duration);
  },

  success(msg) { this.show(msg, "success"); },
  error(msg) { this.show(msg, "danger"); },
  warning(msg) { this.show(msg, "warning"); },
  info(msg) { this.show(msg, "info"); }
};

// Modal Helper
const Modal = {
  open(modalId) {
    const el = document.getElementById(modalId);
    if (el) {
      el.classList.add("open");
    }
  },
  close(modalId) {
    const el = document.getElementById(modalId);
    if (el) {
      el.classList.remove("open");
    }
  }
};

// Multi-stage AI Loading Overlay
const AILoader = {
  el: null,
  subtitleEl: null,
  intervalId: null,

  init() {
    this.el = document.getElementById("aiLoaderOverlay");
    this.subtitleEl = document.getElementById("aiLoaderSubtitle");
  },

  show(messages = [
    "Analyzing study material...",
    "Extracting key concepts...",
    "Formulating exam topics...",
    "Calibrating questions and explanations..."
  ]) {
    this.init();
    if (!this.el) return;

    this.el.classList.add("open");
    let index = 0;
    if (this.subtitleEl) {
      this.subtitleEl.textContent = messages[0];
    }

    if (this.intervalId) clearInterval(this.intervalId);
    this.intervalId = setInterval(() => {
      index = (index + 1) % messages.length;
      if (this.subtitleEl) {
        this.subtitleEl.style.opacity = "0";
        setTimeout(() => {
          this.subtitleEl.textContent = messages[index];
          this.subtitleEl.style.opacity = "1";
        }, 150);
      }
    }, 2500);
  },

  hide() {
    this.init();
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    if (this.el) {
      this.el.classList.remove("open");
    }
  }
};

// Utility formatters
const Utils = {
  formatDate(dateStr) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  },
  truncate(text, max = 100) {
    if (!text || text.length <= max) return text;
    return text.substring(0, max) + "...";
  }
};

window.Toast = Toast;
window.Modal = Modal;
window.AILoader = AILoader;
window.Utils = Utils;
