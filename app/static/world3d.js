/**
 * Offline Ofrenda Keeper — 3D WebGL Altar & Memorial Sanctuary Engine
 * Built with Three.js (locally hosted). 100% offline, zero CDN calls.
 */

(function () {
  "use strict";

  // Check WebGL availability
  function isWebGLAvailable() {
    try {
      const canvas = document.createElement("canvas");
      return !!(window.WebGLRenderingContext && (canvas.getContext("webgl") || canvas.getContext("experimental-webgl")));
    } catch (e) {
      return false;
    }
  }

  if (!isWebGLAvailable() || typeof THREE === "undefined") {
    console.info("WebGL not active or Three.js missing; falling back to 2D canvas.");
    return;
  }

  const canvas = document.getElementById("webgl-canvas");
  if (!canvas) return;

  // Scene setup
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x09060d, 0.075);

  // Camera setup
  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 2.0, 7.2);

  // Renderer setup
  const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x09060d, 1);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;

  // Camera Targets for Step Choreography
  const CAMERA_VIEWS = {
    hero: { pos: new THREE.Vector3(0, 1.85, 7.0), target: new THREE.Vector3(0, 1.25, 0) },
    step1: { pos: new THREE.Vector3(-1.4, 2.0, 5.4), target: new THREE.Vector3(0.2, 1.65, 0) },
    step2: { pos: new THREE.Vector3(1.5, 1.45, 5.0), target: new THREE.Vector3(-0.3, 0.95, 0) },
    step3: { pos: new THREE.Vector3(0, 1.6, 4.8), target: new THREE.Vector3(0, 1.35, 0) },
    step4: { pos: new THREE.Vector3(0, 1.9, 6.2), target: new THREE.Vector3(0, 1.4, 0) },
  };

  let currentViewName = "hero";
  let targetCamPos = CAMERA_VIEWS.hero.pos.clone();
  let targetLookAt = CAMERA_VIEWS.hero.target.clone();
  let currentLookAt = CAMERA_VIEWS.hero.target.clone();

  // Mouse Parallax
  const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
  const raycaster = new THREE.Raycaster();
  const mouseVec = new THREE.Vector2();

  // Color Palette Constants
  const PALETTE = {
    bgDeep: 0x09060d,
    midnightPurple: 0x160d20,
    darkPlum: 0x24152e,
    marigold: 0xff9a27,
    antiqueGold: 0xffd166,
    cempasuchilMagenta: 0xe52b70,
    warmCandlelight: 0xffba42,
    candleWax: 0xf5ebdd,
  };

  // Group for the 3D Altar and all sacred elements
  const altarGroup = new THREE.Group();
  scene.add(altarGroup);

  // --- LIGHTING ---
  const ambientLight = new THREE.AmbientLight(PALETTE.midnightPurple, 0.85);
  scene.add(ambientLight);

  const moonLight = new THREE.DirectionalLight(0xb9aabd, 0.45);
  moonLight.position.set(3, 8, 4);
  scene.add(moonLight);

  // Dynamic Candle Point Lights
  const candleLights = [];
  function createCandleLight(x, y, z, color = PALETTE.warmCandlelight, intensity = 1.4) {
    const light = new THREE.PointLight(color, intensity, 4.5, 2.0);
    light.position.set(x, y, z);
    light.userData = {
      baseIntensity: intensity,
      seed: Math.random() * 100,
      active: true,
    };
    altarGroup.add(light);
    candleLights.push(light);
    return light;
  }

  // --- 3D ALTAR ARCHITECTURE ---

  // Tier Materials
  const altarWoodMaterial = new THREE.MeshStandardMaterial({
    color: 0x1a0f24,
    roughness: 0.75,
    metalness: 0.15,
  });

  const goldTrimMaterial = new THREE.MeshStandardMaterial({
    color: PALETTE.antiqueGold,
    roughness: 0.35,
    metalness: 0.85,
    emissive: 0x3d2b00,
  });

  const clothRunnerMaterial = new THREE.MeshStandardMaterial({
    color: 0x5a1036,
    roughness: 0.85,
    metalness: 0.05,
  });

  // Step 3 (Base Tier)
  const tier3Geo = new THREE.BoxGeometry(4.2, 0.35, 2.4);
  const tier3Mesh = new THREE.Mesh(tier3Geo, altarWoodMaterial);
  tier3Mesh.position.set(0, 0.175, 0);
  altarGroup.add(tier3Mesh);

  // Tier 3 Velvet Runner
  const runner3 = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.36, 2.42), clothRunnerMaterial);
  runner3.position.set(0, 0.18, 0);
  altarGroup.add(runner3);

  // Step 2 (Middle Tier)
  const tier2Geo = new THREE.BoxGeometry(3.2, 0.4, 1.6);
  const tier2Mesh = new THREE.Mesh(tier2Geo, altarWoodMaterial);
  tier2Mesh.position.set(0, 0.55, -0.3);
  altarGroup.add(tier2Mesh);

  const runner2 = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.41, 1.62), clothRunnerMaterial);
  runner2.position.set(0, 0.555, -0.3);
  altarGroup.add(runner2);

  // Step 1 (Summit Tier)
  const tier1Geo = new THREE.BoxGeometry(2.0, 0.45, 1.0);
  const tier1Mesh = new THREE.Mesh(tier1Geo, altarWoodMaterial);
  tier1Mesh.position.set(0, 0.975, -0.6);
  altarGroup.add(tier1Mesh);

  // Golden Edging Strips
  const trims = [
    { w: 4.22, y: 0.35, z: 1.2 },
    { w: 3.22, y: 0.75, z: 0.5 },
    { w: 2.02, y: 1.2, z: -0.1 },
  ];
  trims.forEach((t) => {
    const trim = new THREE.Mesh(new THREE.BoxGeometry(t.w, 0.035, 0.035), goldTrimMaterial);
    trim.position.set(0, t.y, t.z);
    altarGroup.add(trim);
  });

  // --- SACRED CEMPASÚCHIL ARCH (Behind Altar) ---
  const archCurve = new THREE.EllipseCurve(0, 0, 1.6, 2.2, 0, Math.PI, false, 0);
  const archPoints = archCurve.getPoints(36);
  const archGeo = new THREE.BufferGeometry().setFromPoints(archPoints);

  const archGroup = new THREE.Group();
  archGroup.position.set(0, 1.1, -1.05);

  // Create clusters of marigold blossoms along the arch
  const flowerGeo = new THREE.DodecahedronGeometry(0.09, 1);
  const flowerOrangeMat = new THREE.MeshStandardMaterial({
    color: PALETTE.marigold,
    roughness: 0.8,
    emissive: 0x4a2200,
  });
  const flowerGoldMat = new THREE.MeshStandardMaterial({
    color: PALETTE.antiqueGold,
    roughness: 0.8,
    emissive: 0x4a3a00,
  });
  const flowerMagentaMat = new THREE.MeshStandardMaterial({
    color: PALETTE.cempasuchilMagenta,
    roughness: 0.8,
    emissive: 0x3d0016,
  });

  archPoints.forEach((pt, i) => {
    const clusterCount = 3;
    for (let c = 0; c < clusterCount; c++) {
      const mat = (i + c) % 3 === 0 ? flowerGoldMat : (i + c) % 3 === 1 ? flowerOrangeMat : flowerMagentaMat;
      const flower = new THREE.Mesh(flowerGeo, mat);
      flower.position.set(
        pt.x + (Math.random() - 0.5) * 0.16,
        pt.y + (Math.random() - 0.5) * 0.16,
        (Math.random() - 0.5) * 0.18
      );
      flower.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
      archGroup.add(flower);
    }
  });
  altarGroup.add(archGroup);

  // --- MEMORIAL PORTRAIT FRAME (Summit Tier) ---
  const frameGroup = new THREE.Group();
  frameGroup.position.set(0, 1.85, -0.65);

  const outerFrameMesh = new THREE.Mesh(new THREE.BoxGeometry(1.05, 1.3, 0.08), goldTrimMaterial);
  frameGroup.add(outerFrameMesh);

  // Default Canvas Texture for Portrait (Abuela Rosa / Placeholder)
  const portraitCanvas = document.createElement("canvas");
  portraitCanvas.width = 512;
  portraitCanvas.height = 640;
  const pctx = portraitCanvas.getContext("2d");
  function renderDefaultPortrait() {
    pctx.fillStyle = "#1e1327";
    pctx.fillRect(0, 0, 512, 640);

    const grad = pctx.createRadialGradient(256, 260, 40, 256, 260, 240);
    grad.addColorStop(0, "#ffd166");
    grad.addColorStop(0.5, "#ff9a27");
    grad.addColorStop(1, "#160d20");
    pctx.fillStyle = grad;
    pctx.beginPath();
    pctx.arc(256, 250, 120, 0, Math.PI * 2);
    pctx.fill();

    pctx.font = "bold 130px serif";
    pctx.fillStyle = "#09060d";
    pctx.textAlign = "center";
    pctx.textBaseline = "middle";
    pctx.fillText("🕯️", 256, 250);

    pctx.font = "italic 32px Georgia";
    pctx.fillStyle = "#f5ebdd";
    pctx.fillText("In Loving Memory", 256, 480);
    pctx.font = "24px Georgia";
    pctx.fillStyle = "#ffd166";
    pctx.fillText("Día de los Muertos", 256, 524);
  }
  renderDefaultPortrait();

  const portraitTexture = new THREE.CanvasTexture(portraitCanvas);
  const portraitMat = new THREE.MeshStandardMaterial({
    map: portraitTexture,
    roughness: 0.65,
    metalness: 0.1,
  });

  const photoMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.88, 1.12), portraitMat);
  photoMesh.position.z = 0.045;
  frameGroup.add(photoMesh);

  altarGroup.add(frameGroup);

  // Method to update 3D frame when user uploads a photo
  window.update3DPortrait = function (imgElementOrUrl) {
    if (typeof imgElementOrUrl === "string") {
      const img = new Image();
      img.onload = () => {
        pctx.drawImage(img, 0, 0, 512, 640);
        portraitTexture.needsUpdate = true;
      };
      img.src = imgElementOrUrl;
    } else if (imgElementOrUrl instanceof HTMLImageElement) {
      pctx.drawImage(imgElementOrUrl, 0, 0, 512, 640);
      portraitTexture.needsUpdate = true;
    }
  };

  // --- REALISTIC 3D CANDLES WITH ANIMATED FLAMES ---
  const candleObjects = [];
  const candleWaxMat = new THREE.MeshStandardMaterial({
    color: PALETTE.candleWax,
    roughness: 0.45,
    metalness: 0.05,
  });
  const candleWickMat = new THREE.MeshBasicMaterial({ color: 0x24152e });

  // Flame Geometry: Teardrop cone
  const flameGeo = new THREE.ConeGeometry(0.045, 0.16, 12);
  flameGeo.translate(0, 0.08, 0);

  // Flame Shader Material for warm inner/outer glow
  function createFlameMaterial() {
    return new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        colorInner: { value: new THREE.Color(PALETTE.antiqueGold) },
        colorOuter: { value: new THREE.Color(PALETTE.marigold) },
      },
      vertexShader: `
        uniform float time;
        varying vec2 vUv;
        void main() {
          vUv = uv;
          vec3 pos = position;
          // Flickering wind wave along y height
          float wave = sin(time * 12.0 + pos.y * 14.0) * 0.02 * (pos.y / 0.16);
          float waveZ = cos(time * 9.0 + pos.y * 10.0) * 0.015 * (pos.y / 0.16);
          pos.x += wave;
          pos.z += waveZ;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 colorInner;
        uniform vec3 colorOuter;
        varying vec2 vUv;
        void main() {
          float dist = abs(vUv.x - 0.5) * 2.0;
          vec3 col = mix(colorInner, colorOuter, dist);
          float alpha = smoothstep(1.0, 0.2, vUv.y) * smoothstep(1.0, 0.1, dist);
          gl_FragColor = vec4(col, alpha * 0.92);
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
  }

  function addCandle(x, y, z, height = 0.35) {
    const candle = new THREE.Group();
    candle.position.set(x, y, z);

    // Wax Body
    const bodyGeo = new THREE.CylinderGeometry(0.075, 0.078, height, 16);
    const body = new THREE.Mesh(bodyGeo, candleWaxMat);
    body.position.y = height / 2;
    candle.add(body);

    // Wick
    const wick = new THREE.Mesh(new THREE.CylinderGeometry(0.007, 0.007, 0.05, 8), candleWickMat);
    wick.position.y = height + 0.025;
    candle.add(wick);

    // Flame
    const flameMat = createFlameMaterial();
    const flame = new THREE.Mesh(flameGeo, flameMat);
    flame.position.y = height + 0.035;
    candle.add(flame);

    // Light
    const light = createCandleLight(x, y + height + 0.12, z, PALETTE.warmCandlelight, 1.35);

    candle.userData = {
      flame,
      flameMat,
      light,
      height,
      lit: true,
    };

    altarGroup.add(candle);
    candleObjects.push(candle);
    return candle;
  }

  // Candle Placements across tiers
  // Summit Tier (Flanking portrait)
  addCandle(-0.7, 1.2, -0.65, 0.42);
  addCandle(0.7, 1.2, -0.65, 0.42);

  // Middle Tier
  addCandle(-1.25, 0.75, -0.28, 0.32);
  addCandle(1.25, 0.75, -0.28, 0.32);
  addCandle(-0.6, 0.75, 0.2, 0.26);
  addCandle(0.6, 0.75, 0.2, 0.26);

  // Base Tier
  addCandle(-1.8, 0.35, 0.45, 0.38);
  addCandle(1.8, 0.35, 0.45, 0.38);
  addCandle(-1.1, 0.35, 0.85, 0.24);
  addCandle(1.1, 0.35, 0.85, 0.24);

  // Interactive Candle Toggling on Click
  function toggleCandleState(candle) {
    if (!candle || !candle.userData) return;
    const isLit = !candle.userData.lit;
    candle.userData.lit = isLit;
    candle.userData.flame.visible = isLit;
    candle.userData.light.visible = isLit;

    if (window.OfrendaAudio) {
      if (isLit) {
        window.OfrendaAudio.playCandleLight();
      } else {
        window.OfrendaAudio.playCandleExtinguish();
      }
    }
  }

  // --- TRADITIONAL OFFERINGS (3D Models on Tiers) ---

  // 1. Bread of the Dead (Pan de Muerto)
  const panMat = new THREE.MeshStandardMaterial({
    color: 0x9e5b22,
    roughness: 0.9,
    metalness: 0.05,
  });
  const panSugarMat = new THREE.MeshStandardMaterial({
    color: 0xfff0db,
    roughness: 0.95,
  });

  function createPanDeMuerto(x, y, z, scale = 1.0) {
    const panGroup = new THREE.Group();
    panGroup.position.set(x, y, z);
    panGroup.scale.setScalar(scale);

    const dome = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.55), panMat);
    panGroup.add(dome);

    const bone1 = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.32, 8), panSugarMat);
    bone1.rotation.z = Math.PI / 2;
    bone1.position.y = 0.12;
    panGroup.add(bone1);

    const bone2 = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.32, 8), panSugarMat);
    bone2.rotation.x = Math.PI / 2;
    bone2.position.y = 0.12;
    panGroup.add(bone2);

    const crown = new THREE.Mesh(new THREE.SphereGeometry(0.04, 10, 8), panSugarMat);
    crown.position.y = 0.16;
    panGroup.add(crown);

    altarGroup.add(panGroup);
  }

  createPanDeMuerto(-0.25, 0.75, 0.1, 0.9);
  createPanDeMuerto(0.25, 0.35, 0.85, 0.85);

  // 2. Sugar Skulls (Calaveritas)
  const skullMat = new THREE.MeshStandardMaterial({
    color: 0xfbf6ea,
    roughness: 0.6,
    metalness: 0.1,
  });
  function createSkull(x, y, z, rotY = 0) {
    const skullGroup = new THREE.Group();
    skullGroup.position.set(x, y, z);
    skullGroup.rotation.y = rotY;

    // Cranium
    const cranium = new THREE.Mesh(new THREE.SphereGeometry(0.12, 14, 12), skullMat);
    cranium.scale.set(1.0, 1.1, 1.1);
    skullGroup.add(cranium);

    // Jaw
    const jaw = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.08, 0.12), skullMat);
    jaw.position.set(0, -0.09, 0.04);
    skullGroup.add(jaw);

    // Eye sockets (Magenta floral eyes)
    const eyeMat = new THREE.MeshBasicMaterial({ color: PALETTE.cempasuchilMagenta });
    const eye1 = new THREE.Mesh(new THREE.SphereGeometry(0.028, 8, 8), eyeMat);
    eye1.position.set(-0.045, 0.01, 0.11);
    const eye2 = eye1.clone();
    eye2.position.x = 0.045;
    skullGroup.add(eye1);
    skullGroup.add(eye2);

    altarGroup.add(skullGroup);
  }

  createSkull(-0.25, 0.43, 0.85, 0.25);
  createSkull(0.25, 0.83, 0.15, -0.2);

  // 3. Clay Cup / Mug (Jarro de Barro)
  const clayMat = new THREE.MeshStandardMaterial({
    color: 0x9c3d1b,
    roughness: 0.85,
    metalness: 0.05,
  });
  function createClayCup(x, y, z) {
    const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.055, 0.16, 14), clayMat);
    cup.position.set(x, y + 0.08, z);
    altarGroup.add(cup);
  }
  createClayCup(-0.85, 0.35, 0.6);
  createClayCup(0.85, 0.35, 0.6);

  // --- FLOATING 3D MARIGOLD PETALS ---
  const PETAL_COUNT = 65;
  const petalGeo = new THREE.PlaneGeometry(0.12, 0.18, 2, 2);
  // Curve the plane geometry for organic petal shape
  const posAttr = petalGeo.attributes.position;
  for (let i = 0; i < posAttr.count; i++) {
    const y = posAttr.getY(i);
    posAttr.setZ(i, Math.sin((y + 0.09) * 16.0) * 0.035);
  }
  petalGeo.computeVertexNormals();

  const petalMaterials = [
    new THREE.MeshStandardMaterial({ color: PALETTE.marigold, roughness: 0.7, side: THREE.DoubleSide }),
    new THREE.MeshStandardMaterial({ color: PALETTE.antiqueGold, roughness: 0.7, side: THREE.DoubleSide }),
    new THREE.MeshStandardMaterial({ color: PALETTE.cempasuchilMagenta, roughness: 0.7, side: THREE.DoubleSide }),
  ];

  const petals = [];
  for (let i = 0; i < PETAL_COUNT; i++) {
    const mat = petalMaterials[i % petalMaterials.length];
    const mesh = new THREE.Mesh(petalGeo, mat);

    mesh.position.set(
      (Math.random() - 0.5) * 7.0,
      Math.random() * 5.0 - 0.5,
      (Math.random() - 0.5) * 5.0
    );

    mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);

    const speed = Math.random() * 0.007 + 0.005;
    const swaySpeed = Math.random() * 0.02 + 0.01;
    const swayRadius = Math.random() * 0.015 + 0.005;

    mesh.userData = {
      speed,
      swaySpeed,
      swayRadius,
      rotX: (Math.random() - 0.5) * 0.02,
      rotY: (Math.random() - 0.5) * 0.02,
      rotZ: (Math.random() - 0.5) * 0.02,
      phase: Math.random() * Math.PI * 2,
    };

    scene.add(mesh);
    petals.push(mesh);
  }

  // --- FLOATING GLOWING EMBERS / INCENSE PARTICLES ---
  const EMBER_COUNT = 55;
  const emberGeo = new THREE.BufferGeometry();
  const emberPositions = new Float32Array(EMBER_COUNT * 3);
  const emberVelocities = [];

  for (let i = 0; i < EMBER_COUNT; i++) {
    emberPositions[i * 3] = (Math.random() - 0.5) * 4.5;
    emberPositions[i * 3 + 1] = Math.random() * 4.0;
    emberPositions[i * 3 + 2] = (Math.random() - 0.5) * 3.5;

    emberVelocities.push({
      y: Math.random() * 0.006 + 0.003,
      x: (Math.random() - 0.5) * 0.003,
      z: (Math.random() - 0.5) * 0.003,
    });
  }
  emberGeo.setAttribute("position", new THREE.BufferAttribute(emberPositions, 3));

  const emberMat = new THREE.PointsMaterial({
    color: PALETTE.antiqueGold,
    size: 0.065,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending,
  });

  const emberParticles = new THREE.Points(emberGeo, emberMat);
  scene.add(emberParticles);

  // --- WINDOW RESIZE & MOUSE EVENTS ---
  function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }
  window.addEventListener("resize", onWindowResize, { passive: true });

  function onMouseMove(e) {
    mouse.targetX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouse.targetY = -(e.clientY / window.innerHeight - 0.5) * 2;

    mouseVec.x = (e.clientX / window.innerWidth) * 2 - 1;
    mouseVec.y = -(e.clientY / window.innerHeight) * 2 + 1;
  }
  window.addEventListener("mousemove", onMouseMove, { passive: true });

  // Raycasting on Click for Candle Interactions
  window.addEventListener("click", (e) => {
    // Only process clicks on canvas / background elements
    const targetTag = e.target.tagName.toLowerCase();
    if (["button", "input", "select", "textarea", "a", "label"].includes(targetTag)) {
      return;
    }

    raycaster.setFromCamera(mouseVec, camera);
    const intersects = raycaster.intersectObjects(candleObjects, true);
    if (intersects.length > 0) {
      let root = intersects[0].object;
      while (root.parent && root.parent !== altarGroup) {
        root = root.parent;
      }
      toggleCandleState(root);
    }
  });

  // Step Transition API
  window.setWorld3DStep = function (stepKey) {
    const key = typeof stepKey === "number" ? `step${stepKey}` : stepKey;
    if (CAMERA_VIEWS[key]) {
      currentViewName = key;
      targetCamPos.copy(CAMERA_VIEWS[key].pos);
      targetLookAt.copy(CAMERA_VIEWS[key].target);
    }
  };

  // Visibility change handling
  let isTabActive = true;
  document.addEventListener("visibilitychange", () => {
    isTabActive = !document.hidden;
  });

  // Prefers-reduced-motion check
  let prefersReducedMotion = false;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    prefersReducedMotion = true;
  }

  // --- ANIMATION LOOP ---
  let clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);
    if (!isTabActive) return;

    const delta = clock.getDelta();
    const time = clock.getElapsedTime();

    // 1. Mouse Parallax Damping
    mouse.x += (mouse.targetX - mouse.x) * 0.05;
    mouse.y += (mouse.targetY - mouse.y) * 0.05;

    // 2. Camera Choreography Damping
    const parallaxOffsetX = prefersReducedMotion ? 0 : mouse.x * 0.45;
    const parallaxOffsetY = prefersReducedMotion ? 0 : mouse.y * 0.25;

    camera.position.x += (targetCamPos.x + parallaxOffsetX - camera.position.x) * 0.04;
    camera.position.y += (targetCamPos.y + parallaxOffsetY - camera.position.y) * 0.04;
    camera.position.z += (targetCamPos.z - camera.position.z) * 0.04;

    currentLookAt.x += (targetLookAt.x - currentLookAt.x) * 0.04;
    currentLookAt.y += (targetLookAt.y - currentLookAt.y) * 0.04;
    currentLookAt.z += (targetLookAt.z - currentLookAt.z) * 0.04;
    camera.lookAt(currentLookAt);

    // 3. Candle Flame Shaders & Flickering Lights
    candleObjects.forEach((c) => {
      if (c.userData.lit && c.userData.flameMat.uniforms) {
        c.userData.flameMat.uniforms.time.value = time;
      }
    });

    candleLights.forEach((light) => {
      if (light.userData.active && light.visible) {
        const seed = light.userData.seed;
        const flicker = Math.sin(time * 14.0 + seed) * 0.15 + Math.cos(time * 23.0 + seed) * 0.1;
        light.intensity = Math.max(0.6, light.userData.baseIntensity + flicker);
      }
    });

    // 4. Floating Marigold Petals Animation
    if (!prefersReducedMotion) {
      petals.forEach((p) => {
        p.userData.phase += p.userData.swaySpeed;
        p.position.y -= p.userData.speed;
        p.position.x += Math.sin(p.userData.phase) * p.userData.swayRadius;
        p.position.z += Math.cos(p.userData.phase) * p.userData.swayRadius * 0.5;

        p.rotation.x += p.userData.rotX;
        p.rotation.y += p.userData.rotY;
        p.rotation.z += p.userData.rotZ;

        // Reset when falling below floor level
        if (p.position.y < -0.4) {
          p.position.y = 4.5 + Math.random() * 1.5;
          p.position.x = (Math.random() - 0.5) * 6.5;
          p.position.z = (Math.random() - 0.5) * 5.0;
        }
      });

      // 5. Floating Glowing Embers
      const positions = emberParticles.geometry.attributes.position.array;
      for (let i = 0; i < EMBER_COUNT; i++) {
        const idx = i * 3;
        positions[idx + 1] += emberVelocities[i].y;
        positions[idx] += Math.sin(time * 2.0 + i) * 0.002;

        if (positions[idx + 1] > 4.5) {
          positions[idx + 1] = 0.1;
          positions[idx] = (Math.random() - 0.5) * 3.5;
          positions[idx + 2] = (Math.random() - 0.5) * 3.0;
        }
      }
      emberParticles.geometry.attributes.position.needsUpdate = true;
    }

    renderer.render(scene, camera);
  }

  animate();
})();
