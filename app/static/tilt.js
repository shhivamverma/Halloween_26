/**
 * Offline Ofrenda Keeper — 3D Perspective Tilt & Specular Shine Engine
 * Pure vanilla JavaScript 3D card physics for hackathon-winning UI/UX.
 */

(function () {
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  function initTilt() {
    const tiltElements = document.querySelectorAll("[data-tilt]");

    tiltElements.forEach((el) => {
      // Add shine overlay if not present
      if (!el.querySelector(".tilt-shine")) {
        const shine = document.createElement("div");
        shine.className = "tilt-shine";
        el.style.position = el.style.position || "relative";
        el.appendChild(shine);
      }

      el.addEventListener("mousemove", (e) => {
        const rect = el.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const percentX = (x / rect.width) * 100;
        const percentY = (y / rect.height) * 100;

        // Max tilt angle (degrees)
        const maxTilt = parseFloat(el.getAttribute("data-tilt-max")) || 5.0;

        const tiltY = ((x - centerX) / centerX) * maxTilt;
        const tiltX = -((y - centerY) / centerY) * maxTilt;

        el.style.setProperty("--shine-x", `${percentX}%`);
        el.style.setProperty("--shine-y", `${percentY}%`);

        el.style.transform = `perspective(1000px) rotateX(${tiltX.toFixed(2)}deg) rotateY(${tiltY.toFixed(2)}deg) scale3d(1.008, 1.008, 1.008)`;
      });

      el.addEventListener("mouseleave", () => {
        el.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
      });
    });
  }

  window.initTilt = initTilt;
  document.addEventListener("DOMContentLoaded", initTilt);
})();
