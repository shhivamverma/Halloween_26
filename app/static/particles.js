/**
 * Offline Ofrenda Keeper — 3D Cempasúchil & Golden Embers Particle Engine
 * Fully offline, zero-dependency HTML5 3D perspective particle system.
 */

(function () {
  const canvas = document.getElementById("ambient-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  let isEnabled = true;
  let mouse = { x: width / 2, y: height / 2, vx: 0, vy: 0, lastX: width / 2, lastY: height / 2 };
  let particles = [];
  const FOV = 450;
  const PETAL_COUNT = 38;
  const EMBER_COUNT = 24;

  const PETAL_COLORS = [
    { base: "#f28c28", highlight: "#ffa726", shadow: "#c45a05" }, // Marigold orange
    { base: "#ffd54f", highlight: "#fff59d", shadow: "#e6b000" }, // Saffron gold
    { base: "#d81b60", highlight: "#f06292", shadow: "#880e4f" }, // Papel magenta
  ];

  class Petal3D {
    constructor() {
      this.reset(true);
    }

    reset(initial = false) {
      this.x = (Math.random() - 0.5) * width * 1.6;
      this.y = initial ? (Math.random() - 0.5) * height * 1.6 : -height * 0.8;
      this.z = Math.random() * 600 + 50;

      this.size = Math.random() * 12 + 10;
      this.speedY = Math.random() * 1.2 + 0.8;
      this.speedX = (Math.random() - 0.5) * 0.6;

      this.rotX = Math.random() * Math.PI * 2;
      this.rotY = Math.random() * Math.PI * 2;
      this.rotZ = Math.random() * Math.PI * 2;

      this.rotSpeedX = (Math.random() - 0.5) * 0.03;
      this.rotSpeedY = (Math.random() - 0.5) * 0.04;
      this.rotSpeedZ = (Math.random() - 0.5) * 0.02;

      this.sway = Math.random() * Math.PI * 2;
      this.swaySpeed = Math.random() * 0.02 + 0.01;
      this.color = PETAL_COLORS[Math.floor(Math.random() * PETAL_COLORS.length)];
    }

    update() {
      this.sway += this.swaySpeed;
      this.x += this.speedX + Math.sin(this.sway) * 0.8;
      this.y += this.speedY;

      // 3D rotations
      this.rotX += this.rotSpeedX;
      this.rotY += this.rotSpeedY;
      this.rotZ += this.rotSpeedZ;

      // Subtle mouse breeze interaction
      const scale = FOV / (FOV + this.z);
      const screenX = width / 2 + this.x * scale;
      const screenY = height / 2 + this.y * scale;

      const dx = screenX - mouse.x;
      const dy = screenY - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 140) {
        const force = (1 - dist / 140) * 2.5;
        this.x += (dx / (dist || 1)) * force * 4;
        this.y += (dy / (dist || 1)) * force * 4;
        this.rotSpeedX += (Math.random() - 0.5) * 0.05;
      }

      // Wrap around bounds
      if (this.y * scale > height * 0.7 || screenY > height + 50) {
        this.reset(false);
      }
    }

    draw(ctx) {
      const scale = FOV / (FOV + this.z);
      if (scale <= 0) return;

      const screenX = width / 2 + this.x * scale;
      const screenY = height / 2 + this.y * scale;

      if (screenX < -60 || screenX > width + 60 || screenY < -60 || screenY > height + 60) return;

      ctx.save();
      ctx.translate(screenX, screenY);
      ctx.rotate(this.rotZ);

      // 3D perspective squash based on pitch & yaw
      const cosX = Math.cos(this.rotX);
      const cosY = Math.cos(this.rotY);
      ctx.scale(scale * Math.abs(cosY), scale * Math.abs(cosX));

      // Draw curved marigold petal geometry
      const r = this.size;
      ctx.beginPath();
      ctx.moveTo(0, -r);
      ctx.bezierCurveTo(r * 0.75, -r * 0.7, r * 0.9, r * 0.4, 0, r);
      ctx.bezierCurveTo(-r * 0.9, r * 0.4, -r * 0.75, -r * 0.7, 0, -r);
      ctx.closePath();

      // Shading based on orientation
      const facing = cosX * cosY;
      const grad = ctx.createLinearGradient(-r * 0.5, -r, r * 0.5, r);
      if (facing > 0) {
        grad.addColorStop(0, this.color.highlight);
        grad.addColorStop(0.6, this.color.base);
        grad.addColorStop(1, this.color.shadow);
      } else {
        grad.addColorStop(0, this.color.base);
        grad.addColorStop(0.5, this.color.shadow);
        grad.addColorStop(1, "#120b18");
      }

      ctx.fillStyle = grad;
      ctx.globalAlpha = Math.min(0.85, Math.max(0.2, scale * 1.1));
      ctx.fill();

      // Subtle central vein highlight
      ctx.beginPath();
      ctx.moveTo(0, -r * 0.8);
      ctx.lineTo(0, r * 0.6);
      ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.restore();
    }
  }

  class Ember3D {
    constructor() {
      this.reset(true);
    }

    reset(initial = false) {
      this.x = (Math.random() - 0.5) * width * 1.2;
      this.y = initial ? Math.random() * height : height + 20;
      this.z = Math.random() * 400 + 50;
      this.radius = Math.random() * 2 + 1;
      this.speedY = -(Math.random() * 0.8 + 0.4);
      this.speedX = (Math.random() - 0.5) * 0.4;
      this.life = Math.random() * 100 + 50;
      this.maxLife = this.life;
      this.hue = Math.random() > 0.4 ? 42 : 28; // Candle gold or warm amber
    }

    update() {
      this.y += this.speedY;
      this.x += this.speedX + Math.sin(this.y * 0.02) * 0.3;
      this.life--;
      if (this.life <= 0 || this.y < -20) {
        this.reset(false);
      }
    }

    draw(ctx) {
      const scale = FOV / (FOV + this.z);
      const screenX = width / 2 + this.x * scale;
      const screenY = this.y;

      const alpha = (this.life / this.maxLife) * 0.7;
      ctx.save();
      ctx.beginPath();
      ctx.arc(screenX, screenY, this.radius * scale, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${this.hue}, 100%, 70%, ${alpha})`;
      ctx.shadowBlur = 8 * scale;
      ctx.shadowColor = `hsla(${this.hue}, 100%, 60%, ${alpha * 0.8})`;
      ctx.fill();
      ctx.restore();
    }
  }

  function initParticles() {
    particles = [];
    for (let i = 0; i < PETAL_COUNT; i++) {
      particles.push(new Petal3D());
    }
    for (let i = 0; i < EMBER_COUNT; i++) {
      particles.push(new Ember3D());
    }
  }

  function onResize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }

  function onMouseMove(e) {
    mouse.vx = e.clientX - mouse.lastX;
    mouse.vy = e.clientY - mouse.lastY;
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    mouse.lastX = e.clientX;
    mouse.lastY = e.clientY;
  }

  let animationFrameId = null;
  function animate() {
    if (!isEnabled) return;
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      particles[i].update();
      particles[i].draw(ctx);
    }

    animationFrameId = requestAnimationFrame(animate);
  }

  window.toggleAmbientParticles = function (forceState) {
    if (typeof forceState === "boolean") {
      isEnabled = forceState;
    } else {
      isEnabled = !isEnabled;
    }
    if (isEnabled) {
      if (!animationFrameId) animate();
    } else {
      ctx.clearRect(0, 0, width, height);
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
    }
    return isEnabled;
  };

  window.addEventListener("resize", onResize, { passive: true });
  window.addEventListener("mousemove", onMouseMove, { passive: true });

  // Honor prefers-reduced-motion
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    isEnabled = false;
  }

  initParticles();
  if (isEnabled) {
    animate();
  }
})();
