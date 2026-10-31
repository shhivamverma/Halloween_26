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
    intro: { pos: new THREE.Vector3(0, 2.3, 7.8), target: new THREE.Vector3(0, 1.25, 0) },
    hero: { pos: new THREE.Vector3(0, 1.85, 6.8), target: new THREE.Vector3(0, 1.25, 0) },
    step1: { pos: new THREE.Vector3(-1.4, 2.0, 5.4), target: new THREE.Vector3(0.2, 1.65, 0) },
    step2: { pos: new THREE.Vector3(1.5, 1.45, 5.0), target: new THREE.Vector3(-0.3, 0.95, 0) },
    step3: { pos: new THREE.Vector3(-1.3, 1.75, 4.8), target: new THREE.Vector3(0.3, 1.45, 0) },
    step4: { pos: new THREE.Vector3(1.3, 1.65, 4.8), target: new THREE.Vector3(-0.2, 1.4, 0) },
    step5: { pos: new THREE.Vector3(0, 1.55, 4.5), target: new THREE.Vector3(0, 1.35, 0) },
    step6: { pos: new THREE.Vector3(0, 1.9, 6.2), target: new THREE.Vector3(0, 1.4, 0) },
  };

  let currentViewName = "intro";
  let targetCamPos = CAMERA_VIEWS.intro.pos.clone();
  let targetLookAt = CAMERA_VIEWS.intro.target.clone();
  let currentLookAt = CAMERA_VIEWS.intro.target.clone();

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

  // --- PROCEDURAL 3D HUMAN HANDS (Anatomical proportions & articulated joints) ---
  const skinMaterial = new THREE.MeshStandardMaterial({
    color: 0xdfab8e,
    roughness: 0.65,
    metalness: 0.05,
    emissive: 0x221108,
    emissiveIntensity: 0.15,
  });

  function buildHumanHand(isLeft = false) {
    const handRoot = new THREE.Group();

    // Forearm / Wrist
    const forearmGeo = new THREE.CylinderGeometry(0.13, 0.16, 0.75, 16);
    const forearm = new THREE.Mesh(forearmGeo, skinMaterial);
    forearm.position.y = 0.55;
    handRoot.add(forearm);

    // Palm
    const palmGeo = new THREE.BoxGeometry(0.42, 0.48, 0.14, 4, 4, 4);
    const palm = new THREE.Mesh(palmGeo, skinMaterial);
    palm.position.y = 0.08;
    handRoot.add(palm);

    // Finger definitions: [xOffset, baseAngleZ, length, radius]
    const fingerDefs = [
      { name: "index", x: (isLeft ? 0.14 : -0.14), zRot: 0.03, len: 0.22, rad: 0.042 },
      { name: "middle", x: (isLeft ? 0.05 : -0.05), zRot: 0.0, len: 0.25, rad: 0.044 },
      { name: "ring", x: (isLeft ? -0.05 : 0.05), zRot: -0.03, len: 0.22, rad: 0.042 },
      { name: "pinky", x: (isLeft ? -0.14 : 0.14), zRot: -0.08, len: 0.18, rad: 0.036 },
    ];

    const fingerJoints = [];

    fingerDefs.forEach((fd) => {
      // Proximal joint (attached to palm)
      const pJoint = new THREE.Group();
      pJoint.position.set(fd.x, -0.18, 0.02);
      pJoint.rotation.z = isLeft ? fd.zRot : -fd.zRot;
      palm.add(pJoint);

      const pMesh = new THREE.Mesh(new THREE.CylinderGeometry(fd.rad * 0.95, fd.rad, fd.len * 0.45, 10), skinMaterial);
      pMesh.position.y = -fd.len * 0.225;
      pJoint.add(pMesh);

      // Intermediate joint
      const mJoint = new THREE.Group();
      mJoint.position.y = -fd.len * 0.45;
      pJoint.add(mJoint);

      const mMesh = new THREE.Mesh(new THREE.CylinderGeometry(fd.rad * 0.85, fd.rad * 0.95, fd.len * 0.35, 10), skinMaterial);
      mMesh.position.y = -fd.len * 0.175;
      mJoint.add(mMesh);

      // Distal joint & rounded fingertip
      const dJoint = new THREE.Group();
      dJoint.position.y = -fd.len * 0.35;
      mJoint.add(dJoint);

      const dMesh = new THREE.Mesh(new THREE.CylinderGeometry(fd.rad * 0.7, fd.rad * 0.85, fd.len * 0.25, 10), skinMaterial);
      dMesh.position.y = -fd.len * 0.125;
      dJoint.add(dMesh);

      const tipMesh = new THREE.Mesh(new THREE.SphereGeometry(fd.rad * 0.7, 8, 8), skinMaterial);
      tipMesh.position.y = -fd.len * 0.25;
      dJoint.add(tipMesh);

      fingerJoints.push({ pJoint, mJoint, dJoint });
    });

    // Articulated Thumb
    const thumbRoot = new THREE.Group();
    thumbRoot.position.set(isLeft ? 0.24 : -0.24, -0.02, 0.04);
    thumbRoot.rotation.z = isLeft ? 0.6 : -0.6;
    thumbRoot.rotation.y = isLeft ? -0.4 : 0.4;
    palm.add(thumbRoot);

    const thumb1 = new THREE.Mesh(new THREE.CylinderGeometry(0.048, 0.055, 0.2, 10), skinMaterial);
    thumb1.position.y = -0.1;
    thumbRoot.add(thumb1);

    const thumbJoint2 = new THREE.Group();
    thumbJoint2.position.y = -0.2;
    thumbRoot.add(thumbJoint2);

    const thumb2 = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.048, 0.16, 10), skinMaterial);
    thumb2.position.y = -0.08;
    thumbJoint2.add(thumb2);

    const thumbTip = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 8), skinMaterial);
    thumbTip.position.y = -0.16;
    thumbJoint2.add(thumbTip);

    // Controller method to interpolate fingers between cupped holding and released open poses
    handRoot.userData = {
      setPose(progress) {
        // progress: 0.0 = cupped hold; 1.0 = fully open graceful release
        const curlX = THREE.MathUtils.lerp(1.15, 0.1, progress);
        const curlThumb = THREE.MathUtils.lerp(0.85, 0.15, progress);

        fingerJoints.forEach((fj) => {
          fj.pJoint.rotation.x = curlX * 0.55;
          fj.mJoint.rotation.x = curlX * 0.45;
          fj.dJoint.rotation.x = curlX * 0.35;
        });

        thumbRoot.rotation.x = curlThumb * 0.6;
        thumbJoint2.rotation.x = curlThumb * 0.5;
      },
    };

    handRoot.userData.setPose(0.0);
    return handRoot;
  }

  // Hands Group for the Intro Sequence
  const introHandsGroup = new THREE.Group();
  const leftHand = buildHumanHand(true);
  const rightHand = buildHumanHand(false);
  leftHand.position.set(-0.38, 4.4, 4.0);
  leftHand.rotation.set(0.4, 0.35, 0.25);
  rightHand.position.set(0.38, 4.4, 4.0);
  rightHand.rotation.set(0.4, -0.35, -0.25);

  introHandsGroup.add(leftHand);
  introHandsGroup.add(rightHand);
  introHandsGroup.visible = false;
  scene.add(introHandsGroup);

  // --- OFFERING PETALS (Held in hands, released in Phase A) ---
  const OFFERING_PETAL_COUNT = 34;
  const offeringPetals = [];
  const offeringPetalsGroup = new THREE.Group();
  scene.add(offeringPetalsGroup);

  for (let i = 0; i < OFFERING_PETAL_COUNT; i++) {
    const mat = petalMaterials[i % petalMaterials.length];
    const petal = new THREE.Mesh(petalGeo, mat);
    petal.scale.setScalar(0.9);
    petal.visible = false;
    petal.userData = {
      active: false,
      vy: 0,
      vx: 0,
      vz: 0,
      rotX: 0,
      rotY: 0,
      rotZ: 0,
      swayRate: 0,
      swayAmp: 0,
      phase: 0,
      landed: false,
      targetY: 0.72 + Math.random() * 0.35,
    };
    offeringPetalsGroup.add(petal);
    offeringPetals.push(petal);
  }

  function initOfferingPetalsInHands() {
    offeringPetals.forEach((p, idx) => {
      p.visible = true;
      p.userData.active = true;
      p.userData.landed = false;
      p.userData.vy = -0.005 - Math.random() * 0.006;
      p.userData.vx = (Math.random() - 0.5) * 0.012;
      p.userData.vz = (Math.random() - 0.5) * 0.01;
      p.userData.rotX = (Math.random() - 0.5) * 0.05;
      p.userData.rotY = (Math.random() - 0.5) * 0.05;
      p.userData.rotZ = (Math.random() - 0.5) * 0.05;
      p.userData.swayRate = 0.04 + Math.random() * 0.03;
      p.userData.swayAmp = 0.01 + Math.random() * 0.012;
      p.userData.phase = Math.random() * Math.PI * 2;

      // Position clustered between the cupped palms
      p.position.set(
        (Math.random() - 0.5) * 0.32,
        2.05 + (Math.random() - 0.5) * 0.12,
        3.95 + (Math.random() - 0.5) * 0.15
      );
      p.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
    });
  }

  function updateFallingOfferingPetals(delta) {
    offeringPetals.forEach((p) => {
      if (!p.userData.active || p.userData.landed) return;

      p.userData.vy -= 0.00035; // Gentle downward gravity
      p.position.y += p.userData.vy;
      p.userData.phase += p.userData.swayRate;
      p.position.x += Math.sin(p.userData.phase) * p.userData.swayAmp + p.userData.vx;
      p.position.z += p.userData.vz;

      p.rotation.x += p.userData.rotX;
      p.rotation.y += p.userData.rotY;
      p.rotation.z += p.userData.rotZ;

      // Settle on the altar
      if (p.position.y <= p.userData.targetY) {
        p.position.y = p.userData.targetY;
        p.userData.landed = true;
        p.rotation.x = Math.PI * 0.5 + (Math.random() - 0.5) * 0.2;
      }
    });
  }

  // Interactive Sacred Petal Shower API
  window.offerSacredPetals = function (count = 24) {
    if (window.OfrendaAudio) {
      window.OfrendaAudio.playFlowerScatter();
      window.OfrendaAudio.playChime(659.25, 2.2);
    }
    for (let i = 0; i < count; i++) {
      const mat = petalMaterials[i % petalMaterials.length];
      const p = new THREE.Mesh(petalGeo, mat);
      p.scale.setScalar(0.7 + Math.random() * 0.5);
      p.position.set(
        (Math.random() - 0.5) * 3.4,
        3.5 + Math.random() * 1.8,
        (Math.random() - 0.5) * 2.2
      );
      p.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI);
      p.userData = {
        active: true,
        vy: -0.012 - Math.random() * 0.014,
        vx: (Math.random() - 0.5) * 0.014,
        vz: (Math.random() - 0.5) * 0.012,
        rotX: (Math.random() - 0.5) * 0.06,
        rotY: (Math.random() - 0.5) * 0.06,
        rotZ: (Math.random() - 0.5) * 0.06,
        swayRate: 0.03 + Math.random() * 0.04,
        swayAmp: 0.012 + Math.random() * 0.016,
        phase: Math.random() * Math.PI * 2,
        landed: false,
        targetY: 0.2 + Math.random() * 0.9,
      };
      offeringPetalsGroup.add(p);
      offeringPetals.push(p);
    }

    // Gentle altar illumination pulse on petal offering
    if (altarBloomLight) {
      altarBloomLight.intensity = 2.8;
      setTimeout(() => {
        altarBloomLight.intensity = 1.6;
      }, 900);
    }
  };

  // --- VOLUMETRIC GOLDEN LIGHT RAYS & CENTER ALTAR BLOOM ---
  const altarBloomLight = new THREE.PointLight(PALETTE.antiqueGold, 0.0, 9.0, 1.8);
  altarBloomLight.position.set(0, 1.35, 0.2);
  altarGroup.add(altarBloomLight);

  const volumetricRaysGroup = new THREE.Group();
  volumetricRaysGroup.position.set(0, 1.0, -0.2);

  const rayMat = new THREE.MeshBasicMaterial({
    color: 0xffd166,
    transparent: true,
    opacity: 0.0,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  const rayCount = 8;
  for (let i = 0; i < rayCount; i++) {
    const angle = (i / rayCount) * Math.PI;
    const rayPlane = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 4.2), rayMat);
    rayPlane.position.y = 1.8;
    rayPlane.rotation.y = angle;
    rayPlane.rotation.z = (Math.random() - 0.5) * 0.35;
    volumetricRaysGroup.add(rayPlane);
  }
  scene.add(volumetricRaysGroup);

  // --- CINEMATIC MEMORIAL INTRO ANIMATION CONTROLLER ---
  let introSequenceActive = false;
  let introSequenceStartTime = 0;
  let introOnCompleteCallback = null;
  let introPhase = 0; // 0 = idle, 1 = Phase A, 2 = Phase B, 3 = Phase C

  window.startMemorialIntroSequence = function (onComplete) {
    introSequenceActive = true;
    introSequenceStartTime = clock.getElapsedTime();
    introOnCompleteCallback = onComplete;
    introPhase = 1;
    introHandsGroup.visible = true;

    // Reset hands pose and position
    leftHand.userData.setPose(0.0);
    rightHand.userData.setPose(0.0);
    leftHand.position.set(-0.38, 4.4, 4.0);
    rightHand.position.set(0.38, 4.4, 4.0);

    // Reset offering petals
    initOfferingPetalsInHands();

    // Reset bloom light and rays
    altarBloomLight.intensity = 0.0;
    rayMat.opacity = 0.0;

    // Camera targets Phase A close-in
    targetCamPos.set(0, 1.95, 5.0);
    targetLookAt.set(0, 1.25, 0);

    // Play soft sound cue
    if (window.OfrendaAudio) {
      window.OfrendaAudio.playIntroFanfare();
    }
  };

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

    // Hover cursor feedback over interactive candles
    const targetTag = e.target.tagName.toLowerCase();
    if (targetTag === "canvas") {
      raycaster.setFromCamera(mouseVec, camera);
      const intersects = raycaster.intersectObjects(candleObjects, true);
      canvas.style.cursor = intersects.length > 0 ? "pointer" : "default";
    }
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

    // Intro Sequence Phase Progression
    if (introSequenceActive) {
      const elapsed = time - introSequenceStartTime;

      if (elapsed < 3.2) {
        // Phase A: Hands descent & Petal release
        introPhase = 1;
        const descentProgress = Math.min(1.0, elapsed / 1.5);
        const handY = THREE.MathUtils.lerp(4.4, 2.15, descentProgress);
        leftHand.position.y = handY;
        rightHand.position.y = handY;

        if (elapsed > 1.4) {
          const openProgress = Math.min(1.0, (elapsed - 1.4) / 1.1);
          leftHand.userData.setPose(openProgress);
          rightHand.userData.setPose(openProgress);
          updateFallingOfferingPetals(delta);
        }
      } else if (elapsed < 5.5) {
        // Phase B: Bloom illumination, volumetric light rays & warm glow
        introPhase = 2;
        const retreatProgress = Math.min(1.0, (elapsed - 3.2) / 1.6);
        leftHand.position.y = THREE.MathUtils.lerp(2.15, 4.8, retreatProgress);
        rightHand.position.y = THREE.MathUtils.lerp(2.15, 4.8, retreatProgress);
        if (retreatProgress >= 1.0) introHandsGroup.visible = false;

        updateFallingOfferingPetals(delta);

        const bloomProgress = Math.min(1.0, (elapsed - 3.2) / 1.4);
        altarBloomLight.intensity = THREE.MathUtils.lerp(0.0, 4.5, bloomProgress);
        rayMat.opacity = Math.min(0.35, bloomProgress * 0.35) * (0.85 + Math.sin(time * 3.5) * 0.15);
        volumetricRaysGroup.rotation.y += 0.003;

        targetCamPos.set(0, 1.85, 4.8);
      } else if (elapsed < 7.0) {
        // Phase C: Transition bloom & Reveal Main Website
        introPhase = 3;
        targetCamPos.set(0, 1.85, 4.4);
        if (introOnCompleteCallback) {
          const cb = introOnCompleteCallback;
          introOnCompleteCallback = null;
          cb();
        }
      } else {
        introSequenceActive = false;
        introHandsGroup.visible = false;
        altarBloomLight.intensity = 1.8;
        rayMat.opacity = 0.08;
      }
    }

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

