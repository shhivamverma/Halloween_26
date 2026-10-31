/**
 * Offline Ofrenda Keeper — Immersive Memorial Sound & Ambience System
 * 100% Offline Procedural Soundscapes powered by Web Audio API.
 * Zero external audio downloads, zero latency, pure procedural beauty.
 */

(function () {
  "use strict";

  // Audio State & Preferences
  const STORAGE_KEY = "ofrenda_sound_settings_v1";
  const state = {
    enabled: false,
    masterVolume: 0.75,
    musicVolume: 0.6,
    sfxVolume: 0.7,
    ambientVolume: 0.5,
    isInitialized: false,
  };

  // Restore saved preferences
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (typeof parsed.enabled === "boolean") state.enabled = parsed.enabled;
      if (typeof parsed.masterVolume === "number") state.masterVolume = parsed.masterVolume;
      if (typeof parsed.musicVolume === "number") state.musicVolume = parsed.musicVolume;
      if (typeof parsed.sfxVolume === "number") state.sfxVolume = parsed.sfxVolume;
      if (typeof parsed.ambientVolume === "number") state.ambientVolume = parsed.ambientVolume;
    }
  } catch (e) {
    console.warn("Audio preferences read warning:", e);
  }

  function savePreferences() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          enabled: state.enabled,
          masterVolume: state.masterVolume,
          musicVolume: state.musicVolume,
          sfxVolume: state.sfxVolume,
          ambientVolume: state.ambientVolume,
        })
      );
    } catch (e) {
      // ignore
    }
  }

  // Web Audio Context & Node Hierarchy
  let ctx = null;
  let masterGain = null;
  let musicGain = null;
  let sfxGain = null;
  let ambientGain = null;

  // Active Sound Generators
  let windNoiseNode = null;
  let candleCrackleInterval = null;
  let musicInterval = null;
  let activeDroneOscs = [];

  function ensureContext() {
    if (!ctx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return null;
      ctx = new AudioContextClass();

      // Master output
      masterGain = ctx.createGain();
      masterGain.gain.setValueAtTime(state.enabled ? state.masterVolume : 0, ctx.currentTime);
      masterGain.connect(ctx.destination);

      // Sub-busses
      musicGain = ctx.createGain();
      musicGain.gain.setValueAtTime(state.musicVolume, ctx.currentTime);
      musicGain.connect(masterGain);

      sfxGain = ctx.createGain();
      sfxGain.gain.setValueAtTime(state.sfxVolume, ctx.currentTime);
      sfxGain.connect(masterGain);

      ambientGain = ctx.createGain();
      ambientGain.gain.setValueAtTime(state.ambientVolume, ctx.currentTime);
      ambientGain.connect(masterGain);

      state.isInitialized = true;
    }

    if (ctx.state === "suspended") {
      ctx.resume().catch(() => {});
    }
    return ctx;
  }

  // --- AMBIENT SOUND GENERATORS ---

  // 1. Procedural Wind Ambience (Swept filtered pink noise)
  function startWindAmbience() {
    if (!ctx || windNoiseNode) return;

    try {
      const bufferSize = ctx.sampleRate * 3;
      const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const output = noiseBuffer.getChannelData(0);
      let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;

      // Pink noise algorithm
      for (let i = 0; i < bufferSize; i++) {
        const white = Math.random() * 2 - 1;
        b0 = 0.99886 * b0 + white * 0.0555179;
        b1 = 0.99332 * b1 + white * 0.0750759;
        b2 = 0.96900 * b2 + white * 0.1538520;
        b3 = 0.86650 * b3 + white * 0.3104856;
        b4 = 0.55000 * b4 + white * 0.5329522;
        b5 = -0.7616 * b5 - white * 0.0168980;
        output[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.04;
        b6 = white * 0.115926;
      }

      const whiteNoise = ctx.createBufferSource();
      whiteNoise.buffer = noiseBuffer;
      whiteNoise.loop = true;

      // Lowpass filter for deep midnight breeze
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(260, ctx.currentTime);

      // Slow LFO for gentle wind swell
      const lfo = ctx.createOscillator();
      lfo.frequency.setValueAtTime(0.08, ctx.currentTime);
      const lfoGain = ctx.createGain();
      lfoGain.gain.setValueAtTime(90, ctx.currentTime);
      lfo.connect(lfoGain);
      lfoGain.connect(filter.frequency);
      lfo.start();

      whiteNoise.connect(filter);
      filter.connect(ambientGain);
      whiteNoise.start();

      windNoiseNode = { source: whiteNoise, lfo, filter };
    } catch (e) {
      console.warn("Wind ambience error:", e);
    }
  }

  function stopWindAmbience() {
    if (windNoiseNode) {
      try {
        windNoiseNode.source.stop();
        windNoiseNode.lfo.stop();
        windNoiseNode.source.disconnect();
      } catch (e) {}
      windNoiseNode = null;
    }
  }

  // 2. Procedural Candle Flame Crackle
  function startCandleCrackle() {
    if (candleCrackleInterval) return;

    candleCrackleInterval = setInterval(() => {
      if (!state.enabled || !ctx || ctx.state !== "running") return;
      // Random micro crackles
      if (Math.random() < 0.45) {
        triggerCrackleBurst();
      }
    }, 400);
  }

  function triggerCrackleBurst() {
    if (!ctx) return;
    try {
      const duration = 0.015 + Math.random() * 0.025;
      const buffer = ctx.createBuffer(1, Math.floor(ctx.sampleRate * duration), ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < data.length; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (data.length * 0.3));
      }

      const source = ctx.createBufferSource();
      source.buffer = buffer;

      const bandpass = ctx.createBiquadFilter();
      bandpass.type = "bandpass";
      bandpass.frequency.setValueAtTime(1800 + Math.random() * 1200, ctx.currentTime);
      bandpass.Q.setValueAtTime(3.5, ctx.currentTime);

      const burstGain = ctx.createGain();
      burstGain.gain.setValueAtTime(0.06 + Math.random() * 0.08, ctx.currentTime);

      source.connect(bandpass);
      bandpass.connect(burstGain);
      burstGain.connect(ambientGain);

      source.start();
    } catch (e) {}
  }

  function stopCandleCrackle() {
    if (candleCrackleInterval) {
      clearInterval(candleCrackleInterval);
      candleCrackleInterval = null;
    }
  }

  // 3. Meditative Memorial Music (Warm Pentatonic Drone Harmonics)
  // Notes corresponding to D minor pentatonic: D3, F3, G3, A3, C4, D4
  const CHORD_PROGRESSIONS = [
    [146.83, 220.00, 261.63, 349.23], // Dm7 (D3, A3, C4, F4)
    [130.81, 196.00, 261.63, 329.63], // Cmaj (C3, G3, C4, E4)
    [116.54, 174.61, 233.08, 293.66], // Bbmaj (Bb2, F3, Bb3, D4)
    [110.00, 164.81, 220.00, 261.63], // Am (A2, E3, A3, C4)
  ];
  let currentChordIndex = 0;

  function startAmbientMusic() {
    if (activeDroneOscs.length > 0 || !ctx) return;
    playNextChord();
    musicInterval = setInterval(playNextChord, 8000);
  }

  function playNextChord() {
    if (!state.enabled || !ctx || ctx.state !== "running") return;
    try {
      const chord = CHORD_PROGRESSIONS[currentChordIndex];
      currentChordIndex = (currentChordIndex + 1) % CHORD_PROGRESSIONS.length;

      // Create warm additive sine/triangle pads
      const fadeDuration = 7.5;
      const now = ctx.currentTime;

      chord.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const oscGain = ctx.createGain();
        const filter = ctx.createBiquadFilter();

        osc.type = idx % 2 === 0 ? "sine" : "triangle";
        // Subtle detuning for warm acoustic richness
        osc.frequency.setValueAtTime(freq * (1 + (idx - 1.5) * 0.002), now);

        filter.type = "lowpass";
        filter.frequency.setValueAtTime(650 + idx * 120, now);

        // Smooth swelling attack and decay
        oscGain.gain.setValueAtTime(0.0001, now);
        oscGain.gain.exponentialRampToValueAtTime(0.045 / chord.length, now + 3.0);
        oscGain.gain.exponentialRampToValueAtTime(0.0001, now + fadeDuration);

        osc.connect(filter);
        filter.connect(oscGain);
        oscGain.connect(musicGain);

        osc.start(now);
        osc.stop(now + fadeDuration);

        activeDroneOscs.push(osc);
      });

      // Periodic cleanup of stopped oscillators
      setTimeout(() => {
        activeDroneOscs = activeDroneOscs.filter((o) => {
          try {
            return o.playbackState !== 3;
          } catch (e) {
            return false;
          }
        });
      }, fadeDuration * 1000);
    } catch (e) {
      console.warn("Music chord note:", e);
    }
  }

  function stopAmbientMusic() {
    if (musicInterval) {
      clearInterval(musicInterval);
      musicInterval = null;
    }
    activeDroneOscs.forEach((osc) => {
      try {
        osc.stop();
        osc.disconnect();
      } catch (e) {}
    });
    activeDroneOscs = [];
  }

  // --- SOUND EFFECTS (SFX) ---

  // Soft Magical Chime (Crystal Bell)
  function playChime(freq = 587.33, duration = 2.4) {
    if (!state.enabled || !ensureContext()) return;
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now);

      osc2.type = "sine";
      osc2.frequency.setValueAtTime(freq * 2.76, now); // Metallic overtone

      const filter = ctx.createBiquadFilter();
      filter.type = "bandpass";
      filter.frequency.setValueAtTime(freq, now);
      filter.Q.setValueAtTime(2.0, now);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.18, now + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

      osc.connect(filter);
      osc2.connect(filter);
      filter.connect(gain);
      gain.connect(sfxGain);

      osc.start(now);
      osc2.start(now);
      osc.stop(now + duration);
      osc2.stop(now + duration);
    } catch (e) {}
  }

  // Gentle Candle Flame Lighting
  function playCandleLight() {
    if (!state.enabled || !ensureContext()) return;
    try {
      const now = ctx.currentTime;
      // Soft spark / whoosh
      const duration = 0.35;
      const buffer = ctx.createBuffer(1, Math.floor(ctx.sampleRate * duration), ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < data.length; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (data.length * 0.4));
      }

      const noise = ctx.createBufferSource();
      noise.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = "bandpass";
      filter.frequency.setValueAtTime(400, now);
      filter.frequency.exponentialRampToValueAtTime(1400, now + duration);

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

      noise.connect(filter);
      filter.connect(gain);
      gain.connect(sfxGain);

      noise.start(now);

      // Harmonious warmth bell
      playChime(440, 1.8);
    } catch (e) {}
  }

  // Soft Candle Extinguish (Puff / Smoke)
  function playCandleExtinguish() {
    if (!state.enabled || !ensureContext()) return;
    try {
      const now = ctx.currentTime;
      const duration = 0.25;
      const buffer = ctx.createBuffer(1, Math.floor(ctx.sampleRate * duration), ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < data.length; i++) {
        data[i] = (Math.random() * 2 - 1) * (1 - i / data.length);
      }

      const noise = ctx.createBufferSource();
      noise.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(700, now);
      filter.frequency.exponentialRampToValueAtTime(200, now + duration);

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

      noise.connect(filter);
      filter.connect(gain);
      gain.connect(sfxGain);

      noise.start(now);
    } catch (e) {}
  }

  // Subtle Wooden / Marimba Button Tap
  function playButtonClick() {
    if (!state.enabled || !ensureContext()) return;
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "triangle";
      osc.frequency.setValueAtTime(320, now);
      osc.frequency.exponentialRampToValueAtTime(110, now + 0.06);

      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.06);

      osc.connect(gain);
      gain.connect(sfxGain);

      osc.start(now);
      osc.stop(now + 0.06);
    } catch (e) {}
  }

  // Celestial Altar Reveal Fanfare (Warm Harp Arpeggio & Choir Swell)
  function playReveal() {
    if (!state.enabled || !ensureContext()) return;
    const arpeggio = [293.66, 369.99, 440.00, 587.33, 739.99, 880.00]; // D, F#, A, D, F#, A
    arpeggio.forEach((f, idx) => {
      setTimeout(() => {
        playChime(f, 3.2);
      }, idx * 140);
    });
  }

  // Typing Resonance Glow
  let lastTypingSoundTime = 0;
  function playTypeSound() {
    if (!state.enabled || !ensureContext()) return;
    const now = Date.now();
    if (now - lastTypingSoundTime < 180) return; // rate limit typing ticks
    lastTypingSoundTime = now;

    try {
      const audioNow = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      const notes = [440, 493.88, 554.37, 659.25];
      const pitch = notes[Math.floor(Math.random() * notes.length)];
      osc.frequency.setValueAtTime(pitch, audioNow);

      gain.gain.setValueAtTime(0.012, audioNow);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioNow + 0.15);

      osc.connect(gain);
      gain.connect(sfxGain);

      osc.start(audioNow);
      osc.stop(audioNow + 0.15);
    } catch (e) {}
  }

  // --- PUBLIC API & CONTROLS ---

  function toggleMasterAudio(forceState) {
    ensureContext();
    if (typeof forceState === "boolean") {
      state.enabled = forceState;
    } else {
      state.enabled = !state.enabled;
    }

    if (masterGain && ctx) {
      const now = ctx.currentTime;
      if (state.enabled) {
        masterGain.gain.setValueAtTime(0.001, now);
        masterGain.gain.linearRampToValueAtTime(state.masterVolume, now + 0.5);
        startWindAmbience();
        startCandleCrackle();
        startAmbientMusic();
        playChime(587.33, 1.8);
      } else {
        masterGain.gain.setValueAtTime(masterGain.gain.value, now);
        masterGain.gain.linearRampToValueAtTime(0.0001, now + 0.3);
        stopWindAmbience();
        stopCandleCrackle();
        stopAmbientMusic();
      }
    }

    savePreferences();
    updateUI();
    return state.enabled;
  }

  function setMasterVolume(vol) {
    state.masterVolume = Math.max(0, Math.min(1, vol));
    if (masterGain && ctx && state.enabled) {
      masterGain.gain.setValueAtTime(state.masterVolume, ctx.currentTime);
    }
    savePreferences();
  }

  function setMusicVolume(vol) {
    state.musicVolume = Math.max(0, Math.min(1, vol));
    if (musicGain && ctx) {
      musicGain.gain.setValueAtTime(state.musicVolume, ctx.currentTime);
    }
    savePreferences();
  }

  function setSfxVolume(vol) {
    state.sfxVolume = Math.max(0, Math.min(1, vol));
    if (sfxGain && ctx) {
      sfxGain.gain.setValueAtTime(state.sfxVolume, ctx.currentTime);
    }
    savePreferences();
  }

  function setAmbientVolume(vol) {
    state.ambientVolume = Math.max(0, Math.min(1, vol));
    if (ambientGain && ctx) {
      ambientGain.gain.setValueAtTime(state.ambientVolume, ctx.currentTime);
    }
    savePreferences();
  }

  // Visibility Change Handling (Pause audio when tab is backgrounded)
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      if (ctx && ctx.state === "running") {
        ctx.suspend().catch(() => {});
      }
    } else {
      if (ctx && ctx.state === "suspended" && state.enabled) {
        ctx.resume().catch(() => {});
      }
    }
  });

  function updateUI() {
    const btn = document.getElementById("btn-sound-toggle");
    if (btn) {
      btn.innerHTML = state.enabled
        ? '<span class="sound-icon">🔊</span> <span class="sound-label">Sound: On</span>'
        : '<span class="sound-icon">🔇</span> <span class="sound-label">Sound: Off</span>';
      btn.classList.toggle("sound-active", state.enabled);
      btn.setAttribute("aria-pressed", state.enabled ? "true" : "false");
    }

    const musicSlider = document.getElementById("slider-music-vol");
    if (musicSlider) musicSlider.value = state.musicVolume * 100;

    const sfxSlider = document.getElementById("slider-sfx-vol");
    if (sfxSlider) sfxSlider.value = state.sfxVolume * 100;

    const ambientSlider = document.getElementById("slider-ambient-vol");
    if (ambientSlider) ambientSlider.value = state.ambientVolume * 100;
  }

  // Export to window
  window.OfrendaAudio = {
    state,
    toggleMasterAudio,
    setMasterVolume,
    setMusicVolume,
    setSfxVolume,
    setAmbientVolume,
    playChime,
    playCandleLight,
    playCandleExtinguish,
    playButtonClick,
    playReveal,
    playTypeSound,
    updateUI,
  };

  document.addEventListener("DOMContentLoaded", () => {
    updateUI();
  });
})();
