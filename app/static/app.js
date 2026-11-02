/**
 * Offline Ofrenda Keeper — Frontend Wizard & UI Logic
 * Fully local vanilla JavaScript, no external libraries.
 */

// Application State
const state = {
  currentOfrendaId: null,
  currentStep: 1,
  language: "es", // 'es' or 'en'
  foods: [],
  drinks: [],
  songs: [],
  objects: [],
  mediaRecorder: null,
  audioChunks: [],
  recordInterval: null,
  recordSeconds: 0,
  selectedReferenceFile: null,
  isConvertingVoice: false,
};

// Bilingual UI Text Dictionary
const I18N = {
  en: {
    brandTitle: "Offline Ofrenda Keeper",
    statusOnline: "Running locally. No internet needed",
    statusOllamaDown: "Ollama offline (template fallback ready)",
    statusOffline: "Backend unreachable",
    step1Title: "Who are we honoring?",
    step1Sub: "Begin by entering their name and dates for the altar.",
    step2Title: "Traditional Offerings",
    step2Sub: "Add the favorite foods, drinks, music, and keepsakes they loved.",
    step3Title: "Memories, Voice & Photo",
    step3Sub: "Upload a picture and record or write the stories you want to cherish.",
    step4Title: "Honoring Their Spirit",
    step4Sub: "Generate a warm remembrance using a local AI model and view the completed altar.",
    lblName: "Full Name *",
    lblRelationship: "Relationship to You",
    lblBirthYear: "Birth Year",
    lblDeathYear: "Passing Year",
    lblLanguage: "Altar & Remembrance Language",
    lblFoods: "Favorite Foods (up to 12)",
    lblDrinks: "Favorite Drinks (up to 6)",
    lblSongs: "Songs They Loved (up to 6)",
    lblObjects: "Keepsakes & Cherished Objects (up to 8)",
    lblPhoto: "Portrait Photo",
    lblNoPhoto: "No photo selected",
    lblPhotoHint: "Accepted formats: PNG, JPG, WebP. Photo is saved only on your computer.",
    lblStories: "Written Memories & Stories",
    lblRecordTitle: "Record a Voice Memory (Transcribed Locally via Whisper)",
    lblBtnRecord: "Record Voice Note",
    lblBtnStop: "Stop Recording",
    lblTranscript: "Spoken Memories (Voice Note Transcript)",
    lblTranscriptHint: "Whisper transcribes speech locally on your laptop without sending voice data anywhere.",
    lblModel: "Local AI Model (Ollama)",
    btnGenerateText: "Generate Remembrance",
    loadingCandles: "Lighting the candles...",
    lblRemembrance: "Altar Remembrance (Editable)",
    btnSaveRemembrance: "Save Edits to Remembrance",
    remembranceSaved: "✓ Remembrance updated on altar",
    btnDownload: "📥 Download HTML File",
    btnPrint: "🖨️ Print or Save as PDF",
    btnRegenerate: "🔄 Regenerate",
    drawerTitle: "Saved Ofrendas",
    micDenied: "Microphone access is unavailable or was denied. You can type memories directly above.",
    micRecording: "Recording in progress...",
    micProcessing: "Transcribing locally with Whisper...",
    lblVoiceTitle: "Memorial Voice Recreation (Optional AI Speech)",
    lblVoiceDesc: "Synthesize spoken audio of the remembrance using a family-authorized voice reference.",
    lblVoiceEthicalNotice: "Voice recreation produces an AI simulation for remembrance purposes only. The synthesized speech must never be presented as words actually spoken by the deceased. Explicit permission from the family is required.",
    lblVoiceAuth: "Authorizing Family Member *",
    lblVoiceConsent: "I confirm that I have explicit family permission to synthesize a memorial voice recreation for this ofrenda.",
    lblVoiceRef: "Reference Voice Recording (WAV, MP3, M4A, WebM)",
    btnUseStep3Audio: "Use Step 3 Voice Note",
    lblVoiceLang: "Voice Language",
    btnSynthText: "Synthesize Memorial Voice",
    voiceLoading: "Synthesizing memorial voice locally... This may take a moment.",
    btnDownloadVoice: "📥 Download Voice (.wav)",
    btnDeleteVoice: "Remove Voice",
    voiceBadgeBanner: "AI-Generated Voice Recreation • Memorial Simulation Only (Not spoken by the deceased)",
    voiceRefStatusLoaded: "✓ Reference voice loaded",
    voiceRefStatusNone: "No reference voice loaded yet.",
    btnAmbientOn: "🌸 Petals: On",
    btnAmbientOff: "🌸 Petals: Off",
    lblSuggest: "Suggestions:",
    lblPreviewTitle: "Live Altar Stage Preview",
    lblBtnFullscreen: "Full Altar View",
  },
  es: {
    brandTitle: "Guardián de Ofrendas",
    statusOnline: "Ejecutándose localmente. Sin internet",
    statusOllamaDown: "Ollama desconectado (plantilla activa)",
    statusOffline: "Servidor no disponible",
    step1Title: "¿A quién estamos honrando?",
    step1Sub: "Comienza ingresando su nombre y años para el altar.",
    step2Title: "Ofrendas Tradicionales",
    step2Sub: "Agrega las comidas, bebidas, música y recuerdos que más le gustaban.",
    step3Title: "Memorias, Voz y Foto",
    step3Sub: "Sube un retrato y graba o escribe las anécdotas que deseas recordar.",
    step4Title: "Honrando su Espíritu",
    step4Sub: "Genera un recuerdo amoroso con IA local y contempla el altar terminado.",
    lblName: "Nombre Completo *",
    lblRelationship: "Parentesco / Relación",
    lblBirthYear: "Año de Nacimiento",
    lblDeathYear: "Año de Partida",
    lblLanguage: "Idioma del Altar y Recuerdo",
    lblFoods: "Comidas Favoritas (hasta 12)",
    lblDrinks: "Bebidas Favoritas (hasta 6)",
    lblSongs: "Canciones Preferidas (hasta 6)",
    lblObjects: "Objetos y Recuerdos Especiales (hasta 8)",
    lblPhoto: "Foto de Retrato",
    lblNoPhoto: "Sin foto seleccionada",
    lblPhotoHint: "Formatos permitidos: PNG, JPG, WebP. Tu foto nunca sale de tu equipo.",
    lblStories: "Memorias y Anécdotas Escritas",
    lblRecordTitle: "Grabar Nota de Voz (Transcrita localmente con Whisper)",
    lblBtnRecord: "Grabar Nota de Voz",
    lblBtnStop: "Detener Grabación",
    lblTranscript: "Memorias Habladas (Transcripción)",
    lblTranscriptHint: "Whisper transcribe el audio en tu equipo sin subir tu voz a internet.",
    lblModel: "Modelo Local de IA (Ollama)",
    btnGenerateText: "Generar Recuerdo",
    loadingCandles: "Encendiendo las velas...",
    lblRemembrance: "Recuerdo del Altar (Editable)",
    btnSaveRemembrance: "Guardar Cambios al Recuerdo",
    remembranceSaved: "✓ Recuerdo actualizado en el altar",
    btnDownload: "📥 Descargar Archivo HTML",
    btnPrint: "🖨️ Imprimir o Guardar en PDF",
    btnRegenerate: "🔄 Regenerar",
    drawerTitle: "Ofrendas Guardadas",
    micDenied: "El micrófono no está disponible o el permiso fue denegado. Puedes escribir anécdotas arriba.",
    micRecording: "Grabando memoria...",
    micProcessing: "Transcribiendo localmente con Whisper...",
    lblVoiceTitle: "Recreación de Voz Memorial (Voz IA Opcional)",
    lblVoiceDesc: "Sintetiza la lectura hablada del recuerdo usando una referencia autorizada por la familia.",
    lblVoiceEthicalNotice: "La recreación de voz produce una simulación con IA solo para fines de memoria. La voz sintetizada nunca debe presentarse como palabras dichas por la persona fallecida. Se requiere autorización explícita de la familia.",
    lblVoiceAuth: "Familiar que Autoriza *",
    lblVoiceConsent: "Confirmo que cuento con permiso explícito de la familia para sintetizar una recreación de voz memorial para esta ofrenda.",
    lblVoiceRef: "Grabación de Voz de Referencia (WAV, MP3, M4A, WebM)",
    btnUseStep3Audio: "Usar Nota de Voz del Paso 3",
    lblVoiceLang: "Idioma de la Voz",
    btnSynthText: "Sintetizar Voz Memorial",
    voiceLoading: "Sintetizando voz memorial localmente... Esto puede tomar un momento.",
    btnDownloadVoice: "📥 Descargar Voz (.wav)",
    btnDeleteVoice: "Eliminar Voz",
    voiceBadgeBanner: "Recreación de Voz con IA • Solo Simulación Memorial (No fue hablado por la persona fallecida)",
    voiceRefStatusLoaded: "✓ Voz de referencia cargada",
    voiceRefStatusNone: "Aún no se ha cargado una voz de referencia.",
    btnAmbientOn: "🌸 Pétalos: Sí",
    btnAmbientOff: "🌸 Pétalos: No",
    lblSuggest: "Sugerencias:",
    lblPreviewTitle: "Vista Previa del Altar en Vivo",
    lblBtnFullscreen: "Vista Completa",
  },
};

// DOM References
const elements = {
  statusBadge: document.getElementById("status-badge"),
  statusText: document.getElementById("status-text"),
  btnLangToggle: document.getElementById("btn-lang-toggle"),
  btnOpenDrawer: document.getElementById("btn-open-drawer"),
  btnCloseDrawer: document.getElementById("btn-close-drawer"),
  drawerBackdrop: document.getElementById("drawer-backdrop"),
  drawerList: document.getElementById("drawer-list"),
  btnNewFromDrawer: document.getElementById("btn-new-from-drawer"),
  // Step Panels
  panels: [
    document.getElementById("panel-step-1"),
    document.getElementById("panel-step-2"),
    document.getElementById("panel-step-3"),
    document.getElementById("panel-step-4"),
  ],
  progSteps: [
    document.getElementById("prog-step-1"),
    document.getElementById("prog-step-2"),
    document.getElementById("prog-step-3"),
    document.getElementById("prog-step-4"),
  ],
  // Step 1
  inputName: document.getElementById("input-name"),
  inputRelationship: document.getElementById("input-relationship"),
  inputBirthYear: document.getElementById("input-birth-year"),
  inputDeathYear: document.getElementById("input-death-year"),
  selectLang: document.getElementById("select-lang"),
  btnNext1: document.getElementById("btn-next-1"),
  // Step 2
  inputFood: document.getElementById("input-food"),
  btnAddFood: document.getElementById("btn-add-food"),
  chipsFoods: document.getElementById("chips-foods"),
  inputDrink: document.getElementById("input-drink"),
  btnAddDrink: document.getElementById("btn-add-drink"),
  chipsDrinks: document.getElementById("chips-drinks"),
  inputSong: document.getElementById("input-song"),
  btnAddSong: document.getElementById("btn-add-song"),
  chipsSongs: document.getElementById("chips-songs"),
  inputObject: document.getElementById("input-object"),
  btnAddObject: document.getElementById("btn-add-object"),
  chipsObjects: document.getElementById("chips-objects"),
  btnBack2: document.getElementById("btn-back-2"),
  btnNext2: document.getElementById("btn-next-2"),
  // Step 3
  inputPhoto: document.getElementById("input-photo"),
  photoPreviewBox: document.getElementById("photo-preview-box"),
  textareaStory: document.getElementById("textarea-story"),
  btnRecord: document.getElementById("btn-record"),
  btnStopRecord: document.getElementById("btn-stop-record"),
  recordTimer: document.getElementById("record-timer"),
  recordStatusMsg: document.getElementById("record-status-msg"),
  micGentleMsg: document.getElementById("mic-gentle-msg"),
  textareaTranscript: document.getElementById("textarea-transcript"),
  btnBack3: document.getElementById("btn-back-3"),
  btnNext3: document.getElementById("btn-next-3"),
  // Step 4
  selectModel: document.getElementById("select-model"),
  btnGenerate: document.getElementById("btn-generate"),
  btnGenerateText: document.getElementById("btn-generate-text"),
  generateLoading: document.getElementById("generate-loading"),
  textareaRemembrance: document.getElementById("textarea-remembrance"),
  btnSaveRemembrance: document.getElementById("btn-save-remembrance"),
  remembranceSavedMsg: document.getElementById("remembrance-saved-msg"),
  btnDownloadHtml: document.getElementById("btn-download-html"),
  btnPrintPdf: document.getElementById("btn-print-pdf"),
  btnRegenerate: document.getElementById("btn-regenerate"),
  previewIframe: document.getElementById("preview-iframe"),
  btnBack4: document.getElementById("btn-back-4"),
  btnStartNew: document.getElementById("btn-start-new"),
  // Voice Recreation
  voiceCard: document.getElementById("voice-card"),
  inputVoiceAuth: document.getElementById("input-voice-auth"),
  checkVoiceConsent: document.getElementById("check-voice-consent"),
  inputVoiceRef: document.getElementById("input-voice-ref"),
  btnUseStep3Audio: document.getElementById("btn-use-step3-audio"),
  voiceRefStatus: document.getElementById("voice-ref-status"),
  selectVoiceLang: document.getElementById("select-voice-lang"),
  btnSynthesizeVoice: document.getElementById("btn-synthesize-voice"),
  voiceLoading: document.getElementById("voice-loading"),
  voiceResultBox: document.getElementById("voice-result-box"),
  voiceAudioPlayer: document.getElementById("voice-audio-player"),
  btnDownloadVoice: document.getElementById("btn-download-voice"),
  btnDeleteVoice: document.getElementById("btn-delete-voice"),
  voiceDurationInfo: document.getElementById("voice-duration-info"),
  voiceEngineBadge: document.getElementById("voice-engine-badge"),
  // Hackathon UI & 3D Visualizer Additions
  btnDemoQuick: document.getElementById("btn-demo-quick"),
  btnAmbientToggle: document.getElementById("btn-ambient-toggle"),
  btnFullscreenPreview: document.getElementById("btn-fullscreen-preview"),
  btnCloseFullscreen: document.getElementById("btn-close-fullscreen"),
  previewWrapper: document.getElementById("preview-wrapper"),
  recordWaveCanvas: document.getElementById("record-wave-canvas"),
  voiceSpectrumCanvas: document.getElementById("voice-spectrum-canvas"),
};

// Update UI Language
function setLanguage(lang) {
  state.language = lang;
  elements.selectLang.value = lang;
  const t = I18N[lang] || I18N.en;

  document.getElementById("lbl-brand-title").textContent = t.brandTitle;
  if (elements.btnAmbientToggle) {
    elements.btnAmbientToggle.textContent = ambientState ? t.btnAmbientOn : t.btnAmbientOff;
  }
  if (document.getElementById("lbl-preview-title")) {
    document.getElementById("lbl-preview-title").textContent = t.lblPreviewTitle;
  }
  if (document.getElementById("lbl-btn-fullscreen")) {
    document.getElementById("lbl-btn-fullscreen").textContent = t.lblBtnFullscreen;
  }
  for (let i = 1; i <= 4; i++) {
    const el = document.getElementById(`lbl-suggest-${i}`);
    if (el) el.textContent = t.lblSuggest;
  }
  document.getElementById("step-1-title").textContent = t.step1Title;
  document.getElementById("step-1-sub").textContent = t.step1Sub;
  document.getElementById("step-2-title").textContent = t.step2Title;
  document.getElementById("step-2-sub").textContent = t.step2Sub;
  document.getElementById("step-3-title").textContent = t.step3Title;
  document.getElementById("step-3-sub").textContent = t.step3Sub;
  document.getElementById("step-4-title").textContent = t.step4Title;
  document.getElementById("step-4-sub").textContent = t.step4Sub;

  document.getElementById("lbl-name").textContent = t.lblName;
  document.getElementById("lbl-relationship").textContent = t.lblRelationship;
  document.getElementById("lbl-birth-year").textContent = t.lblBirthYear;
  document.getElementById("lbl-death-year").textContent = t.lblDeathYear;
  document.getElementById("lbl-language").textContent = t.lblLanguage;
  document.getElementById("lbl-foods").textContent = t.lblFoods;
  document.getElementById("lbl-drinks").textContent = t.lblDrinks;
  document.getElementById("lbl-songs").textContent = t.lblSongs;
  document.getElementById("lbl-objects").textContent = t.lblObjects;
  document.getElementById("lbl-photo").textContent = t.lblPhoto;
  document.getElementById("lbl-no-photo").textContent = t.lblNoPhoto;
  document.getElementById("lbl-photo-hint").textContent = t.lblPhotoHint;
  document.getElementById("lbl-stories").textContent = t.lblStories;
  document.getElementById("lbl-record-title").textContent = t.lblRecordTitle;
  document.getElementById("lbl-btn-record").textContent = t.lblBtnRecord;
  document.getElementById("lbl-btn-stop").textContent = t.lblBtnStop;
  document.getElementById("lbl-transcript").textContent = t.lblTranscript;
  document.getElementById("lbl-transcript-hint").textContent = t.lblTranscriptHint;
  document.getElementById("lbl-model").textContent = t.lblModel;
  document.getElementById("btn-generate-text").textContent = t.btnGenerateText;
  document.getElementById("loading-message").textContent = t.loadingCandles;
  document.getElementById("lbl-remembrance").textContent = t.lblRemembrance;
  elements.btnSaveRemembrance.textContent = t.btnSaveRemembrance;
  elements.btnDownloadHtml.textContent = t.btnDownload;
  elements.btnPrintPdf.textContent = t.btnPrint;
  elements.btnRegenerate.textContent = t.btnRegenerate;
  document.getElementById("drawer-title").textContent = t.drawerTitle;

  // Voice Recreation I18N
  if (document.getElementById("lbl-voice-title")) {
    document.getElementById("lbl-voice-title").textContent = t.lblVoiceTitle;
    document.getElementById("lbl-voice-desc").textContent = t.lblVoiceDesc;
    document.getElementById("lbl-voice-ethical-notice").textContent = t.lblVoiceEthicalNotice;
    document.getElementById("lbl-voice-auth").textContent = t.lblVoiceAuth;
    document.getElementById("lbl-voice-consent").textContent = t.lblVoiceConsent;
    document.getElementById("lbl-voice-ref").textContent = t.lblVoiceRef;
    elements.btnUseStep3Audio.textContent = t.btnUseStep3Audio;
    document.getElementById("lbl-voice-lang").textContent = t.lblVoiceLang;
    document.getElementById("btn-synth-text").textContent = t.btnSynthText;
    document.getElementById("voice-loading-message").textContent = t.voiceLoading;
    document.getElementById("lbl-voice-badge-banner").textContent = t.voiceBadgeBanner;
    elements.btnDownloadVoice.textContent = t.btnDownloadVoice;
    elements.btnDeleteVoice.textContent = t.btnDeleteVoice;
  }
}

// Robust Response Parser to eliminate "Unexpected end of JSON input" on proxy/server errors
async function parseJsonResponse(res, defaultError = "Operation failed") {
  let responseText = "";
  try {
    responseText = await res.text();
  } catch (readErr) {
    throw new Error(`${defaultError}: Unable to read response from server.`);
  }

  let data = null;
  if (responseText && responseText.trim().length > 0) {
    try {
      data = JSON.parse(responseText);
    } catch (_) {
      // Body is not JSON (e.g. HTML 502/504 or plain text 500 from reverse proxy)
      if (!res.ok) {
        const clean = responseText.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().slice(0, 240);
        if (res.status === 502 || res.status === 503 || res.status === 504) {
          throw new Error(
            `Server is warming up or processing audio (HTTP ${res.status}). Please wait a few seconds and try again.`
          );
        }
        throw new Error(`${defaultError} (HTTP ${res.status}): ${clean || res.statusText}`);
      }
    }
  }

  if (!res.ok) {
    if (!data) {
      if (res.status === 502 || res.status === 503 || res.status === 504) {
        throw new Error(
          `Server is warming up or processing audio (HTTP ${res.status}). Please wait a few seconds and try again.`
        );
      }
      throw new Error(`${defaultError} (HTTP ${res.status}: ${res.statusText || "Empty response from server"})`);
    }
    const errDetail = data.detail || data.error || data.message || defaultError;
    throw new Error(typeof errDetail === "string" ? errDetail : JSON.stringify(errDetail));
  }

  return data;
}

// Health Check & Model Discovery
async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await parseJsonResponse(res, "Health check failed");

    elements.statusBadge.classList.remove("error");
    if (data.ollama) {
      elements.statusText.textContent = I18N[state.language].statusOnline;
    } else {
      elements.statusText.textContent = I18N[state.language].statusOllamaDown;
    }

    if (data.voice && elements.voiceEngineBadge) {
      const noticeBox = document.getElementById("voice-engine-card-notice");
      const noticeText = document.getElementById("voice-engine-status-text");

      if (data.voice.available) {
        elements.voiceEngineBadge.textContent = `✓ ${data.voice.active_engine || 'Seed-VC'} Ready`;
        elements.voiceEngineBadge.style.color = "var(--success)";
        if (noticeText) {
          noticeText.innerHTML = `<strong>✓ Voice Recreation Ready:</strong> Engine <code>${data.voice.active_engine}</code> is active (Whisper ASR → Kokoro TTS → OpenVoice Tone-Colour Conversion).`;
        }
      } else if (data.voice.status === "insufficient_ram") {
        elements.voiceEngineBadge.textContent = "Requires 2GB RAM";
        elements.voiceEngineBadge.style.color = "var(--candle-gold)";
        if (noticeText) {
          noticeText.innerHTML = `<strong>⚠️ Render Plan Memory Limit:</strong> Container memory is limited to ${data.voice.cgroup_limit_mb || 512} MB (Render Free Tier). XTTS-v2 neural voice synthesis requires at least 2 GB RAM. Upgrade your Render service to the <strong>Starter</strong> (2 GB) plan in the Render dashboard to synthesize voice.`;
        }
      } else {
        elements.voiceEngineBadge.textContent = "Model Setup Needed";
        elements.voiceEngineBadge.style.color = "var(--candle-gold)";
        if (noticeText) {
          noticeText.innerHTML = `<strong>ℹ️ Neural Voice Recreation Model Not Installed:</strong> Voice recreation requires PyTorch, Kokoro, and OpenVoice V2. Install with: <code>pip install -r requirements.txt</code>.`;
        }
      }
    }

    // Populate model selector if models returned
    if (Array.isArray(data.models) && data.models.length > 0) {
      const currentSelected = elements.selectModel.value;
      elements.selectModel.innerHTML = "";
      data.models.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m === data.model ? `${m} (Default)` : m;
        elements.selectModel.appendChild(opt);
      });
      if (data.models.includes(currentSelected)) {
        elements.selectModel.value = currentSelected;
      }
    }
  } catch (err) {
    elements.statusBadge.classList.add("error");
    elements.statusText.textContent = I18N[state.language].statusOffline;
  }
}

// Navigation Between Steps
function goToStep(stepNumber) {
  state.currentStep = stepNumber;
  elements.panels.forEach((p, idx) => {
    if (idx + 1 === stepNumber) {
      p.classList.add("active");
    } else {
      p.classList.remove("active");
    }
  });

  elements.progSteps.forEach((s, idx) => {
    const num = idx + 1;
    s.classList.remove("active", "completed");
    if (num === stepNumber) {
      s.classList.add("active");
    } else if (num < stepNumber) {
      s.classList.add("completed");
    }
  });

  // 3D Altar camera transition & soundscape feedback
  if (window.setWorld3DStep) {
    window.setWorld3DStep(stepNumber);
  }
  if (window.OfrendaAudio) {
    window.OfrendaAudio.playChime();
  }

  // Smooth scroll to wizard
  const heroSection = document.getElementById("section-hero");
  if (heroSection && !heroSection.classList.contains("hidden")) {
    const mainEl = document.querySelector(".main-content");
    if (mainEl) {
      mainEl.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Chip Input Helpers
function renderChips(container, items, arrayRef, maxCount) {
  container.innerHTML = "";
  items.forEach((item, index) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = item;

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "chip-remove";
    removeBtn.innerHTML = "&times;";
    removeBtn.setAttribute("aria-label", `Remove ${item}`);
    removeBtn.addEventListener("click", () => {
      arrayRef.splice(index, 1);
      renderChips(container, arrayRef, arrayRef, maxCount);
    });

    chip.appendChild(removeBtn);
    container.appendChild(chip);
  });
}

function addChip(inputElem, container, arrayRef, maxCount) {
  const val = inputElem.value.trim();
  if (!val) return;
  if (arrayRef.length >= maxCount) {
    alert(`Maximum of ${maxCount} items allowed.`);
    return;
  }
  if (val.length > 60) {
    alert("Item exceeds 60 characters.");
    return;
  }
  arrayRef.push(val);
  inputElem.value = "";
  renderChips(container, arrayRef, arrayRef, maxCount);
}

// Step 1: Create or Update Ofrenda Record
async function saveStep1() {
  const name = elements.inputName.value.trim();
  if (!name) {
    alert("Please enter a name for the ofrenda.");
    elements.inputName.focus();
    return false;
  }

  const birthYear = elements.inputBirthYear.value ? parseInt(elements.inputBirthYear.value, 10) : null;
  const deathYear = elements.inputDeathYear.value ? parseInt(elements.inputDeathYear.value, 10) : null;
  const relationship = elements.inputRelationship.value.trim() || null;
  const language = elements.selectLang.value;

  const payload = {
    name,
    relationship,
    birth_year: birthYear,
    death_year: deathYear,
    language,
    foods: state.foods,
    drinks: state.drinks,
    songs: state.songs,
    objects: state.objects,
  };

  try {
    if (!state.currentOfrendaId) {
      const res = await fetch("/api/ofrendas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Failed to create ofrenda record");
      const record = await res.json();
      state.currentOfrendaId = record.id;
    } else {
      const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Failed to update ofrenda record");
    }
    return true;
  } catch (err) {
    alert("Error saving ofrenda: " + err.message);
    return false;
  }
}

// Step 2: Save Offerings
async function saveStep2() {
  if (!state.currentOfrendaId) return false;
  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        foods: state.foods,
        drinks: state.drinks,
        songs: state.songs,
        objects: state.objects,
      }),
    });
    return res.ok;
  } catch (err) {
    alert("Error saving offerings: " + err.message);
    return false;
  }
}

// Step 3: Save Memories and Transcript
async function saveStep3() {
  if (!state.currentOfrendaId) return false;
  try {
    const storyText = elements.textareaStory.value.trim() || null;
    const transcript = elements.textareaTranscript.value.trim() || null;

    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        story_text: storyText,
        transcript: transcript,
      }),
    });
    return res.ok;
  } catch (err) {
    alert("Error saving memories: " + err.message);
    return false;
  }
}

// Photo Upload Handler
async function handlePhotoSelected(e) {
  const file = e.target.files[0];
  if (!file) return;

  // Local immediate preview
  const reader = new FileReader();
  reader.onload = (event) => {
    elements.photoPreviewBox.innerHTML = `<img src="${event.target.result}" alt="Photo Preview">`;
  };
  reader.readAsDataURL(file);

  // Update 3D WebGL Altar Frame in real time
  if (window.update3DPortrait) {
    window.update3DPortrait(file);
  }
  if (window.OfrendaAudio) {
    window.OfrendaAudio.playCandleLight();
  }

  if (!state.currentOfrendaId) {
    // If user hasn't created the ofrenda yet, create with current name or temporary name
    await saveStep1();
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/photo`, {
      method: "POST",
      body: formData,
    });
    await parseJsonResponse(res, "Failed to upload photo");
  } catch (err) {
    alert("Photo upload error: " + err.message);
  }
}

// Ambient 3D Petal State
let ambientState = true;
function toggleAmbient() {
  if (typeof window.toggleAmbientParticles === "function") {
    ambientState = window.toggleAmbientParticles();
    const t = I18N[state.language];
    if (elements.btnAmbientToggle) {
      elements.btnAmbientToggle.textContent = ambientState ? t.btnAmbientOn : t.btnAmbientOff;
    }
  }
}

// Fullscreen Stage View
function toggleFullscreenAltar(forceOpen) {
  if (!elements.previewWrapper) return;
  if (forceOpen === true) {
    elements.previewWrapper.classList.add("fullscreen");
  } else if (forceOpen === false) {
    elements.previewWrapper.classList.remove("fullscreen");
  } else {
    elements.previewWrapper.classList.toggle("fullscreen");
  }
}

// Offerings Suggestions Cloud Handler
function initSuggestionPills() {
  document.querySelectorAll(".suggestion-pill").forEach((pill) => {
    pill.addEventListener("click", () => {
      const target = pill.getAttribute("data-target");
      const val = pill.getAttribute("data-val");
      if (!val) return;

      if (target === "food") {
        if (state.foods.length < 12 && !state.foods.includes(val)) {
          state.foods.push(val);
          renderChips(elements.chipsFoods, state.foods, state.foods, 12);
        }
      } else if (target === "drink") {
        if (state.drinks.length < 6 && !state.drinks.includes(val)) {
          state.drinks.push(val);
          renderChips(elements.chipsDrinks, state.drinks, state.drinks, 6);
        }
      } else if (target === "song") {
        if (state.songs.length < 6 && !state.songs.includes(val)) {
          state.songs.push(val);
          renderChips(elements.chipsSongs, state.songs, state.songs, 6);
        }
      } else if (target === "object") {
        if (state.objects.length < 8 && !state.objects.includes(val)) {
          state.objects.push(val);
          renderChips(elements.chipsObjects, state.objects, state.objects, 8);
        }
      }
    });
  });
}

// Instant Demo Seeding & Loading ("✨ Demo Abuela Rosa")
async function loadDemoOfrenda() {
  try {
    if (elements.btnDemoQuick) {
      elements.btnDemoQuick.disabled = true;
      elements.btnDemoQuick.textContent = "✨ Loading Demo...";
    }

    const res = await fetch("/api/demo/seed", { method: "POST" });
    if (!res.ok) throw new Error("Failed to seed demo");
    const data = await res.json();

    await openSavedOfrenda(data.id);

    if (elements.btnDemoQuick) {
      elements.btnDemoQuick.textContent = "✓ Demo Loaded!";
      setTimeout(() => {
        elements.btnDemoQuick.textContent = "✨ Demo (Abuela Rosa)";
        elements.btnDemoQuick.disabled = false;
      }, 2500);
    }
  } catch (err) {
    alert("Demo load failed: " + err.message);
    if (elements.btnDemoQuick) {
      elements.btnDemoQuick.textContent = "✨ Demo (Abuela Rosa)";
      elements.btnDemoQuick.disabled = false;
    }
  }
}

// Audio Recording Visualizer (Web Audio API)
let recordAudioCtx = null;
let recordAnalyser = null;
let recordAnimId = null;

function startRecordVisualizer(stream) {
  try {
    const canvas = elements.recordWaveCanvas;
    if (!canvas) return;
    canvas.style.display = "block";
    const ctx = canvas.getContext("2d");

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;

    recordAudioCtx = new AudioContextClass();
    recordAnalyser = recordAudioCtx.createAnalyser();
    recordAnalyser.fftSize = 64;
    const source = recordAudioCtx.createMediaStreamSource(stream);
    source.connect(recordAnalyser);

    const bufferLength = recordAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
      recordAnimId = requestAnimationFrame(draw);
      recordAnalyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = (canvas.width / bufferLength) * 1.6;
      let x = 4;

      for (let i = 0; i < bufferLength; i++) {
        const val = dataArray[i];
        const barHeight = Math.max(3, (val / 255) * canvas.height * 0.85);

        const grad = ctx.createLinearGradient(0, canvas.height, 0, 0);
        grad.addColorStop(0, "#f28c28");
        grad.addColorStop(0.6, "#ffd54f");
        grad.addColorStop(1, "#d81b60");

        ctx.fillStyle = grad;
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 3, barHeight);
        x += barWidth;
      }
    }
    draw();
  } catch (err) {
    console.warn("Visualizer note:", err);
  }
}

function stopRecordVisualizer() {
  if (recordAnimId) {
    cancelAnimationFrame(recordAnimId);
    recordAnimId = null;
  }
  if (elements.recordWaveCanvas) {
    elements.recordWaveCanvas.style.display = "none";
  }
  if (recordAudioCtx && recordAudioCtx.state !== "closed") {
    recordAudioCtx.close().catch(() => {});
  }
}

// Voice Spectrum Visualizer for Playback
let voiceSpectrumAnimId = null;
function startVoiceSpectrumVisualizer() {
  const canvas = elements.voiceSpectrumCanvas;
  if (!canvas) return;
  canvas.style.display = "block";
  const ctx = canvas.getContext("2d");
  const barCount = 28;

  function renderSpectrum() {
    voiceSpectrumAnimId = requestAnimationFrame(renderSpectrum);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / barCount) * 0.8;
    const gap = (canvas.width / barCount) * 0.2;
    const t = Date.now() * 0.006;

    for (let i = 0; i < barCount; i++) {
      const wave = Math.sin(t + i * 0.4) * 0.5 + 0.5;
      const wave2 = Math.cos(t * 1.5 + i * 0.3) * 0.5 + 0.5;
      const height = Math.max(4, (wave * 0.6 + wave2 * 0.4) * canvas.height * 0.85);

      const grad = ctx.createLinearGradient(0, canvas.height, 0, 0);
      grad.addColorStop(0, "#f28c28");
      grad.addColorStop(0.7, "#ffd54f");
      grad.addColorStop(1, "#d81b60");

      const x = i * (barWidth + gap) + gap;
      ctx.fillStyle = grad;
      ctx.fillRect(x, canvas.height - height, barWidth, height);
    }
  }
  renderSpectrum();
}

function stopVoiceSpectrumVisualizer() {
  if (voiceSpectrumAnimId) {
    cancelAnimationFrame(voiceSpectrumAnimId);
    voiceSpectrumAnimId = null;
  }
  if (elements.voiceSpectrumCanvas) {
    elements.voiceSpectrumCanvas.style.display = "none";
  }
}

// Audio Recording via MediaRecorder
async function startRecording() {
  elements.micGentleMsg.textContent = "";
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    elements.micGentleMsg.textContent = I18N[state.language].micDenied;
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.audioChunks = [];
    state.mediaRecorder = new MediaRecorder(stream);
    startRecordVisualizer(stream);

    state.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        state.audioChunks.push(e.data);
      }
    };

    state.mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      stopRecordVisualizer();
      await processRecordedAudio();
    };

    state.mediaRecorder.start();
    state.recordSeconds = 0;
    elements.recordTimer.textContent = "00:00";
    elements.recordTimer.style.display = "inline";
    elements.btnRecord.style.display = "none";
    elements.btnStopRecord.style.display = "inline-flex";
    elements.recordStatusMsg.textContent = I18N[state.language].micRecording;

    state.recordInterval = setInterval(() => {
      state.recordSeconds++;
      const mins = String(Math.floor(state.recordSeconds / 60)).padStart(2, "0");
      const secs = String(state.recordSeconds % 60).padStart(2, "0");
      elements.recordTimer.textContent = `${mins}:${secs}`;
    }, 1000);
  } catch (err) {
    elements.micGentleMsg.textContent = I18N[state.language].micDenied;
  }
}

function stopRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== "inactive") {
    clearInterval(state.recordInterval);
    state.mediaRecorder.stop();
    stopRecordVisualizer();
    elements.btnStopRecord.style.display = "none";
    elements.btnRecord.style.display = "inline-flex";
    elements.recordTimer.style.display = "none";
    elements.recordStatusMsg.textContent = I18N[state.language].micProcessing;
  }
}

async function processRecordedAudio() {
  if (state.audioChunks.length === 0) return;
  const audioBlob = new Blob(state.audioChunks, { type: "audio/webm" });

  if (!state.currentOfrendaId) {
    await saveStep1();
  }

  const formData = new FormData();
  formData.append("file", audioBlob, "voice_note.webm");

  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/audio`, {
      method: "POST",
      body: formData,
    });
    const data = await parseJsonResponse(res, "Audio upload failed");
    elements.recordStatusMsg.textContent = "";

    if (data.text) {
      const current = elements.textareaTranscript.value.trim();
      elements.textareaTranscript.value = current ? `${current}\n\n${data.text}` : data.text;
    } else if (data.warning) {
      elements.recordStatusMsg.textContent = `(${data.warning})`;
    }
  } catch (err) {
    elements.recordStatusMsg.textContent = `Error: ${err.message}`;
  }
}

// Step 4: Generation, Preview, Actions
async function generateRemembrance() {
  if (!state.currentOfrendaId) return;
  await saveStep3();

  const selectedModel = elements.selectModel.value;
  elements.btnGenerate.disabled = true;
  elements.btnRegenerate.disabled = true;
  elements.generateLoading.style.display = "block";

  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: selectedModel }),
    });

    const data = await parseJsonResponse(res, "Remembrance generation failed");

    elements.textareaRemembrance.value = data.remembrance || "";
    updatePreviewIframe();

    // Fanfare banner and celebratory memorial reveal chime
    const fanfare = document.getElementById("altar-fanfare-banner");
    if (fanfare) fanfare.style.display = "flex";
    if (window.OfrendaAudio) {
      window.OfrendaAudio.playReveal();
    }
  } catch (err) {
    alert("Error generating remembrance: " + err.message);
  } finally {
    elements.btnGenerate.disabled = false;
    elements.btnRegenerate.disabled = false;
    elements.generateLoading.style.display = "none";
  }
}

async function saveRemembranceEdits() {
  if (!state.currentOfrendaId) return;
  const text = elements.textareaRemembrance.value.trim();
  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ remembrance: text }),
    });
    if (res.ok) {
      elements.remembranceSavedMsg.textContent = I18N[state.language].remembranceSaved;
      setTimeout(() => {
        elements.remembranceSavedMsg.textContent = "";
      }, 3000);
      updatePreviewIframe();
    }
  } catch (err) {
    alert("Failed to save changes: " + err.message);
  }
}

function updatePreviewIframe() {
  if (state.currentOfrendaId) {
    elements.previewIframe.src = `/api/ofrendas/${state.currentOfrendaId}/page?t=${Date.now()}`;
  }
}

// Step 4: Optional Voice Recreation Handlers
async function handleVoiceRefSelected(e) {
  const file = e.target.files[0];
  if (!file) return;

  const authName = elements.inputVoiceAuth.value.trim();
  const consent = elements.checkVoiceConsent.checked;

  if (!authName || !consent) {
    alert(
      state.language === "es"
        ? "Por favor ingrese el nombre del familiar que autoriza y marque la casilla de consentimiento antes de subir el audio de referencia."
        : "Please enter the authorizing family member's name and check the permission box before uploading reference audio."
    );
    e.target.value = "";
    return;
  }

  if (!state.currentOfrendaId) {
    await saveStep1();
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("authorized_by", authName);
  formData.append("confirmed_permission", "true");

  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/voice/reference`, {
      method: "POST",
      body: formData,
    });
    await parseJsonResponse(res, "Failed to upload reference audio");
    state.selectedReferenceFile = file;
    elements.voiceRefStatus.textContent = I18N[state.language].voiceRefStatusLoaded;
    elements.voiceRefStatus.style.color = "var(--success)";

    // Set preview player
    const previewPlayer = document.getElementById("voice-ref-audio-player");
    const previewContainer = document.getElementById("voice-ref-preview-container");
    if (previewPlayer && previewContainer) {
      previewPlayer.src = URL.createObjectURL(file);
      previewContainer.style.display = "block";
    }

    // Synchronize S2S studio reference display
    const s2sRefStatus = document.getElementById("s2s-ref-file-status");
    const s2sRefPlayer = document.getElementById("s2s-ref-preview-player");
    const s2sRefContainer = document.getElementById("s2s-ref-player-container");
    if (s2sRefStatus) {
      s2sRefStatus.textContent = `✓ Loaded: ${file.name}`;
      s2sRefStatus.style.color = "var(--success)";
    }
    if (s2sRefPlayer && s2sRefContainer) {
      s2sRefPlayer.src = URL.createObjectURL(file);
      s2sRefContainer.style.display = "block";
    }
  } catch (err) {
    alert("Reference upload error: " + err.message);
  }
}

async function handleUseStep3Audio() {
  const authName = elements.inputVoiceAuth.value.trim();
  const consent = elements.checkVoiceConsent.checked;

  if (!authName || !consent) {
    alert(
      state.language === "es"
        ? "Por favor ingrese el nombre del familiar que autoriza y marque la casilla de consentimiento primero."
        : "Please enter the authorizing family member's name and check the permission box first."
    );
    return;
  }

  if (state.audioChunks.length === 0) {
    alert(
      state.language === "es"
        ? "No hay una grabación de audio reciente en el Paso 3. Puede subir un archivo de audio directamente o grabar una nota en el Paso 3."
        : "No recent voice recording found in Step 3. You can upload an audio file directly or record one in Step 3."
    );
    return;
  }

  if (!state.currentOfrendaId) {
    await saveStep1();
  }

  const audioBlob = new Blob(state.audioChunks, { type: "audio/webm" });
  const formData = new FormData();
  formData.append("file", audioBlob, "step3_voice_reference.webm");
  formData.append("authorized_by", authName);
  formData.append("confirmed_permission", "true");

  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/voice/reference`, {
      method: "POST",
      body: formData,
    });
    await parseJsonResponse(res, "Failed to use Step 3 audio");
    elements.voiceRefStatus.textContent = I18N[state.language].voiceRefStatusLoaded;
    elements.voiceRefStatus.style.color = "var(--success)";

    // Set preview player
    const previewPlayer = document.getElementById("voice-ref-audio-player");
    const previewContainer = document.getElementById("voice-ref-preview-container");
    if (previewPlayer && previewContainer) {
      previewPlayer.src = URL.createObjectURL(audioBlob);
      previewContainer.style.display = "block";
    }
  } catch (err) {
    alert("Audio error: " + err.message);
  }
}

async function synthesizeVoice() {
  if (!state.currentOfrendaId) {
    alert(state.language === "es" ? "Cree una ofrenda primero." : "Please create an ofrenda first.");
    return;
  }

  const authName = elements.inputVoiceAuth.value.trim();
  const consent = elements.checkVoiceConsent.checked;

  if (!consent || !authName) {
    alert(
      state.language === "es"
        ? "Debe confirmar el permiso familiar e ingresar el nombre del familiar autorizante."
        : "You must confirm family permission and enter the authorizing family member's name."
    );
    return;
  }

  const remembranceText = elements.textareaRemembrance.value.trim();
  if (!remembranceText) {
    alert(
      state.language === "es"
        ? "Primero debe generar o escribir un recuerdo para el altar."
        : "Please generate or write an altar remembrance first."
    );
    return;
  }

  // Ensure any remembrance edits are persisted
  await saveRemembranceEdits();

  elements.btnSynthesizeVoice.disabled = true;
  const loadingMsg = document.getElementById("voice-loading-message");
  if (loadingMsg) loadingMsg.textContent = "Synthesizing memorial voice locally... This may take a moment.";
  elements.voiceLoading.style.display = "block";

  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/voice/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        authorized_by: authName,
        confirmed_permission: true,
        language: elements.selectVoiceLang.value,
      }),
    });

    const data = await parseJsonResponse(res, "Voice synthesis failed");

    elements.voiceResultBox.style.display = "block";
    elements.voiceAudioPlayer.src = `/api/ofrendas/${state.currentOfrendaId}/voice/audio?t=${Date.now()}`;
    if (data && data.synthesized_duration_s) {
      elements.voiceDurationInfo.textContent = `Duration: ${data.synthesized_duration_s.toFixed(1)}s • Model: ${data.model_used || "Local"}`;
    }
    elements.voiceResultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });

    updatePreviewIframe();
  } catch (err) {
    alert("Voice synthesis error: " + err.message);
  } finally {
    elements.btnSynthesizeVoice.disabled = false;
    elements.voiceLoading.style.display = "none";
  }
}

function downloadSynthesizedVoice() {
  if (!state.currentOfrendaId) return;
  window.location.href = `/api/ofrendas/${state.currentOfrendaId}/voice/download`;
}

async function deleteVoice() {
  if (!state.currentOfrendaId) return;
  if (!confirm(state.language === "es" ? "¿Eliminar la recreación de voz y grabaciones de referencia?" : "Remove synthesized voice recreation and reference files?")) return;

  try {
    const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/voice`, {
      method: "DELETE",
    });
    if (res.ok) {
      elements.voiceResultBox.style.display = "none";
      elements.voiceAudioPlayer.src = "";
      elements.voiceRefStatus.textContent = I18N[state.language].voiceRefStatusNone;
      elements.voiceRefStatus.style.color = "var(--text-muted)";
      elements.inputVoiceRef.value = "";
      elements.voiceDurationInfo.textContent = "";
      updatePreviewIframe();
    }
  } catch (err) {
    alert("Failed to delete voice: " + err.message);
  }
}

// Drawer: Saved Ofrendas
async function loadSavedOfrendas() {
  try {
    const res = await fetch("/api/ofrendas");
    if (!res.ok) return;
    const list = await res.json();

    elements.drawerList.innerHTML = "";
    if (list.length === 0) {
      elements.drawerList.innerHTML = "<p style='color:var(--text-muted);'>No saved ofrendas yet.</p>";
      return;
    }

    list.forEach((item) => {
      const card = document.createElement("div");
      card.className = "ofrenda-item-card";

      const info = document.createElement("div");
      info.innerHTML = `<strong>${item.name}</strong><br><small style="color:var(--text-muted);">${item.relationship || ""}</small>`;

      const actions = document.createElement("div");
      actions.style.display = "flex";
      actions.style.gap = "8px";

      const openBtn = document.createElement("button");
      openBtn.type = "button";
      openBtn.className = "btn btn-secondary";
      openBtn.style.minHeight = "36px";
      openBtn.style.padding = "4px 10px";
      openBtn.textContent = "Open";
      openBtn.addEventListener("click", () => openSavedOfrenda(item.id));

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn btn-danger";
      delBtn.style.minHeight = "36px";
      delBtn.style.padding = "4px 10px";
      delBtn.textContent = "Delete";
      delBtn.addEventListener("click", () => deleteSavedOfrenda(item.id));

      actions.appendChild(openBtn);
      actions.appendChild(delBtn);

      card.appendChild(info);
      card.appendChild(actions);
      elements.drawerList.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading ofrendas", err);
  }
}

async function openSavedOfrenda(id) {
  try {
    const res = await fetch(`/api/ofrendas/${id}`);
    if (!res.ok) return;
    const data = await res.json();

    state.currentOfrendaId = data.id;
    state.language = data.language || "es";
    setLanguage(state.language);

    elements.inputName.value = data.name || "";
    elements.inputRelationship.value = data.relationship || "";
    elements.inputBirthYear.value = data.birth_year || "";
    elements.inputDeathYear.value = data.death_year || "";

    state.foods = data.foods || [];
    state.drinks = data.drinks || [];
    state.songs = data.songs || [];
    state.objects = data.objects || [];

    renderChips(elements.chipsFoods, state.foods, state.foods, 12);
    renderChips(elements.chipsDrinks, state.drinks, state.drinks, 6);
    renderChips(elements.chipsSongs, state.songs, state.songs, 6);
    renderChips(elements.chipsObjects, state.objects, state.objects, 8);

    elements.textareaStory.value = data.story_text || "";
    elements.textareaTranscript.value = data.transcript || "";
    elements.textareaRemembrance.value = data.remembrance || "";

    if (data.photo) {
      elements.photoPreviewBox.innerHTML = `<img src="/api/ofrendas/${data.id}/page" style="display:none;"><div style="color:var(--candle-gold); text-align:center;">✓ Photo loaded</div>`;
    }

    // Load voice profile state if present
    if (data.voice_profile) {
      const vp = data.voice_profile;
      if (vp.authorized_by) {
        elements.inputVoiceAuth.value = vp.authorized_by;
        elements.checkVoiceConsent.checked = true;
      }
      if (vp.has_reference) {
        elements.voiceRefStatus.textContent = I18N[state.language].voiceRefStatusLoaded;
        elements.voiceRefStatus.style.color = "var(--success)";
      } else {
        elements.voiceRefStatus.textContent = I18N[state.language].voiceRefStatusNone;
        elements.voiceRefStatus.style.color = "var(--text-muted)";
      }
      if (vp.has_synthesized_audio) {
        elements.voiceResultBox.style.display = "block";
        elements.voiceAudioPlayer.src = `/api/ofrendas/${data.id}/voice/audio?t=${Date.now()}`;
        if (vp.synthesized_duration_s) {
          elements.voiceDurationInfo.textContent = `Duration: ${vp.synthesized_duration_s.toFixed(1)}s • Model: ${vp.model_used || "Local"}`;
        }
      } else {
        elements.voiceResultBox.style.display = "none";
        elements.voiceAudioPlayer.src = "";
        elements.voiceDurationInfo.textContent = "";
      }
      if (vp.language) {
        elements.selectVoiceLang.value = vp.language;
      }
    } else {
      elements.voiceResultBox.style.display = "none";
      elements.voiceAudioPlayer.src = "";
      elements.inputVoiceAuth.value = "";
      elements.checkVoiceConsent.checked = false;
      elements.voiceRefStatus.textContent = I18N[state.language].voiceRefStatusNone;
      elements.voiceRefStatus.style.color = "var(--text-muted)";
      elements.voiceDurationInfo.textContent = "";
    }

    elements.drawerBackdrop.classList.remove("active");
    const heroSection = document.getElementById("section-hero");
    if (heroSection) heroSection.classList.add("hidden");
    const fanfare = document.getElementById("altar-fanfare-banner");
    if (fanfare && data.remembrance) fanfare.style.display = "flex";
    goToStep(4);
    updatePreviewIframe();
  } catch (err) {
    alert("Error loading ofrenda: " + err.message);
  }
}

async function deleteSavedOfrenda(id) {
  if (!confirm("Are you sure you want to delete this ofrenda?")) return;
  try {
    const res = await fetch(`/api/ofrendas/${id}`, { method: "DELETE" });
    if (res.ok) {
      if (state.currentOfrendaId === id) {
        resetWizard();
      }
      loadSavedOfrendas();
    }
  } catch (err) {
    alert("Delete failed: " + err.message);
  }
}

function resetWizard() {
  state.currentOfrendaId = null;
  state.foods = [];
  state.drinks = [];
  state.songs = [];
  state.objects = [];
  elements.inputName.value = "";
  elements.inputRelationship.value = "";
  elements.inputBirthYear.value = "";
  elements.inputDeathYear.value = "";
  elements.chipsFoods.innerHTML = "";
  elements.chipsDrinks.innerHTML = "";
  elements.chipsSongs.innerHTML = "";
  elements.chipsObjects.innerHTML = "";
  elements.textareaStory.value = "";
  elements.textareaTranscript.value = "";
  elements.textareaRemembrance.value = "";
  elements.photoPreviewBox.innerHTML = `<span class="photo-preview-empty" id="lbl-no-photo">${I18N[state.language].lblNoPhoto}</span>`;
  elements.inputVoiceAuth.value = "";
  elements.checkVoiceConsent.checked = false;
  elements.inputVoiceRef.value = "";
  elements.voiceRefStatus.textContent = I18N[state.language].voiceRefStatusNone;
  elements.voiceRefStatus.style.color = "var(--text-muted)";
  elements.voiceResultBox.style.display = "none";
  elements.voiceAudioPlayer.src = "";
  elements.voiceDurationInfo.textContent = "";

  // Reset S2S studio state
  state.selectedReferenceFile = null;
  state.isConvertingVoice = false;
  s2sRecordedBlob = null;
  const s2sRefInput = document.getElementById("s2s-ref-file-input");
  if (s2sRefInput) s2sRefInput.value = "";
  const s2sRefStatus = document.getElementById("s2s-ref-file-status");
  if (s2sRefStatus) {
    s2sRefStatus.textContent = "No reference file selected";
    s2sRefStatus.style.color = "var(--candle-gold)";
  }
  const s2sRefContainer = document.getElementById("s2s-ref-player-container");
  if (s2sRefContainer) s2sRefContainer.style.display = "none";
  const s2sReviewBox = document.getElementById("s2s-transcript-review-box");
  if (s2sReviewBox) s2sReviewBox.style.display = "none";
  const s2sResultCard = document.getElementById("s2s-result-card");
  if (s2sResultCard) s2sResultCard.style.display = "none";
  const s2sProgress = document.getElementById("s2s-conversion-progress");
  if (s2sProgress) s2sProgress.style.display = "none";
  const s2sUserPreview = document.getElementById("s2s-user-preview-box");
  if (s2sUserPreview) s2sUserPreview.style.display = "none";
  const s2sMicStatus = document.getElementById("s2s-mic-status");
  if (s2sMicStatus) s2sMicStatus.textContent = "";

  elements.previewIframe.src = "about:blank";
  const fanfare = document.getElementById("altar-fanfare-banner");
  if (fanfare) fanfare.style.display = "none";
  if (window.update3DPortrait) window.update3DPortrait(null);
  goToStep(1);
}

// Event Listeners Initialization
function initEventListeners() {
  // --- 3D CINEMATIC INTRO EXPERIENCE & HERO ACTIONS ---
  const btnEnterMemory = document.getElementById("btn-enter-memory");
  const introOverlay = document.getElementById("intro-overlay");
  const transitionBloom = document.getElementById("transition-bloom");

  if (btnEnterMemory) {
    btnEnterMemory.addEventListener("click", () => {
      if (introOverlay) introOverlay.classList.add("hidden");
      if (window.startMemorialIntroSequence) {
        window.startMemorialIntroSequence(() => {
          if (transitionBloom) {
            transitionBloom.classList.add("active");
            setTimeout(() => {
              transitionBloom.classList.remove("active");
            }, 800);
          }
          const hero = document.getElementById("section-hero");
          if (hero) hero.classList.remove("hidden");
          if (window.setWorld3DStep) window.setWorld3DStep("hero");
        });
      } else {
        const hero = document.getElementById("section-hero");
        if (hero) hero.classList.remove("hidden");
        if (window.setWorld3DStep) window.setWorld3DStep("hero");
      }
    });
  }

  const btnReplayIntro = document.getElementById("btn-replay-intro");
  if (btnReplayIntro) {
    btnReplayIntro.addEventListener("click", () => {
      if (introOverlay) introOverlay.classList.remove("hidden");
      if (window.setWorld3DStep) window.setWorld3DStep("intro");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  const heroSection = document.getElementById("section-hero");
  const btnHeroStart = document.getElementById("btn-hero-start");
  if (btnHeroStart) {
    btnHeroStart.addEventListener("click", () => {
      if (heroSection) heroSection.classList.add("hidden");
      goToStep(1);
      if (window.OfrendaAudio) {
        window.OfrendaAudio.playButtonClick();
        window.OfrendaAudio.playChime();
      }
    });
  }

  const btnHeroPetals = document.getElementById("btn-hero-petals");
  if (btnHeroPetals) {
    btnHeroPetals.addEventListener("click", () => {
      if (window.offerSacredPetals) {
        window.offerSacredPetals(24);
      }
    });
  }

  const btnHeroDemo = document.getElementById("btn-hero-demo");
  if (btnHeroDemo) {
    btnHeroDemo.addEventListener("click", () => {
      if (heroSection) heroSection.classList.add("hidden");
      loadDemoOfrenda();
      if (window.OfrendaAudio) {
        window.OfrendaAudio.playButtonClick();
        window.OfrendaAudio.playChime();
      }
    });
  }

  const brandHomeLink = document.getElementById("brand-home-link");
  if (brandHomeLink) {
    brandHomeLink.addEventListener("click", () => {
      if (heroSection) heroSection.classList.remove("hidden");
      if (window.setWorld3DStep) window.setWorld3DStep("hero");
      if (window.OfrendaAudio) window.OfrendaAudio.playChime();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // --- INTEGRATED HEADER SOUNDSCAPE CONTROLS & MIXER PANEL ---
  const btnSoundToggle = document.getElementById("btn-sound-toggle");
  const btnSoundMixerOpen = document.getElementById("btn-sound-mixer-open");
  const soundModal = document.getElementById("sound-modal");
  const btnSoundModalClose = document.getElementById("btn-sound-modal-close");
  const btnSoundMasterToggle = document.getElementById("btn-sound-master-toggle");

  if (btnSoundToggle) {
    btnSoundToggle.addEventListener("click", (e) => {
      e.stopPropagation();
      if (window.OfrendaAudio) {
        window.OfrendaAudio.toggle();
      }
    });
  }

  if (btnSoundMixerOpen) {
    btnSoundMixerOpen.addEventListener("click", (e) => {
      e.stopPropagation();
      if (soundModal) {
        const isOpen = soundModal.classList.toggle("open");
        btnSoundMixerOpen.setAttribute("aria-expanded", isOpen ? "true" : "false");
      }
    });
  }

  if (btnSoundModalClose && soundModal) {
    btnSoundModalClose.addEventListener("click", () => {
      soundModal.classList.remove("open");
      if (btnSoundMixerOpen) btnSoundMixerOpen.setAttribute("aria-expanded", "false");
    });
  }

  document.addEventListener("click", (e) => {
    if (soundModal && soundModal.classList.contains("open")) {
      if (!soundModal.contains(e.target) && !e.target.closest("#btn-sound-mixer-open")) {
        soundModal.classList.remove("open");
        if (btnSoundMixerOpen) btnSoundMixerOpen.setAttribute("aria-expanded", "false");
      }
    }
  });

  if (btnSoundMasterToggle) {
    btnSoundMasterToggle.addEventListener("click", () => {
      if (window.OfrendaAudio) {
        window.OfrendaAudio.toggle();
      }
    });
  }

  const sliderMaster = document.getElementById("slider-vol-master");
  const sliderMusic = document.getElementById("slider-vol-music");
  const sliderAmbience = document.getElementById("slider-vol-ambience");
  const sliderSfx = document.getElementById("slider-vol-sfx");

  if (sliderMaster) {
    sliderMaster.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (window.OfrendaAudio) window.OfrendaAudio.setMasterVolume(val);
    });
  }
  if (sliderMusic) {
    sliderMusic.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (window.OfrendaAudio) window.OfrendaAudio.setMusicVolume(val);
    });
  }
  if (sliderAmbience) {
    sliderAmbience.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (window.OfrendaAudio) window.OfrendaAudio.setAmbientVolume(val);
    });
  }
  if (sliderSfx) {
    sliderSfx.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (window.OfrendaAudio) window.OfrendaAudio.setSfxVolume(val);
    });
  }

  // --- SPEECH-TO-SPEECH (S2S) MICROPHONE RECORDING & CONVERSION ---
  let s2sAudioCtx = null;
  let s2sAnalyser = null;
  let s2sMediaRecorder = null;
  let s2sAudioChunks = [];
  let s2sRecordedBlob = null;
  let s2sWaveAnimId = null;
  let s2sTimerInterval = null;
  let s2sSeconds = 0;

  const s2sWaveCanvas = document.getElementById("s2s-waveform-canvas");
  const btnS2SRecord = document.getElementById("btn-s2s-record");
  const btnS2SStop = document.getElementById("btn-s2s-stop");
  const btnS2SConvert = document.getElementById("btn-s2s-convert");
  const s2sMicTimer = document.getElementById("s2s-mic-timer");
  const s2sMicStatus = document.getElementById("s2s-mic-status");
  const s2sUserPreviewBox = document.getElementById("s2s-user-preview-box");
  const s2sUserAudioPlayer = document.getElementById("s2s-user-audio-player");

  function drawS2SWaveform() {
    if (!s2sAnalyser || !s2sWaveCanvas) return;
    const ctx2d = s2sWaveCanvas.getContext("2d");
    const bufferLength = s2sAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function render() {
      s2sWaveAnimId = requestAnimationFrame(render);
      s2sAnalyser.getByteTimeDomainData(dataArray);

      ctx2d.fillStyle = "#09050e";
      ctx2d.fillRect(0, 0, s2sWaveCanvas.width, s2sWaveCanvas.height);

      ctx2d.lineWidth = 2.5;
      ctx2d.strokeStyle = "#ffd166";
      ctx2d.beginPath();

      const sliceWidth = (s2sWaveCanvas.width * 1.0) / bufferLength;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * s2sWaveCanvas.height) / 2;
        if (i === 0) ctx2d.moveTo(x, y);
        else ctx2d.lineTo(x, y);
        x += sliceWidth;
      }
      ctx2d.lineTo(s2sWaveCanvas.width, s2sWaveCanvas.height / 2);
      ctx2d.stroke();
    }
    render();
  }

  if (btnS2SRecord) {
    btnS2SRecord.addEventListener("click", async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
        s2sAudioCtx = new AudioCtxClass();
        const source = s2sAudioCtx.createMediaStreamSource(stream);
        s2sAnalyser = s2sAudioCtx.createAnalyser();
        s2sAnalyser.fftSize = 1024;
        source.connect(s2sAnalyser);

        s2sAudioChunks = [];
        s2sMediaRecorder = new MediaRecorder(stream);
        s2sMediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) s2sAudioChunks.push(e.data);
        };
        s2sMediaRecorder.onstop = () => {
          stream.getTracks().forEach((track) => track.stop());
          if (s2sWaveAnimId) cancelAnimationFrame(s2sWaveAnimId);
          s2sRecordedBlob = new Blob(s2sAudioChunks, { type: "audio/webm" });
          if (s2sUserAudioPlayer) {
            s2sUserAudioPlayer.src = URL.createObjectURL(s2sRecordedBlob);
            if (s2sUserPreviewBox) s2sUserPreviewBox.style.display = "block";
          }
          triggerS2STranscription();
        };

        s2sMediaRecorder.start();
        btnS2SRecord.style.display = "none";
        btnS2SStop.style.display = "inline-flex";
        if (s2sMicTimer) {
          s2sMicTimer.style.display = "block";
          s2sSeconds = 0;
          s2sTimerInterval = setInterval(() => {
            s2sSeconds++;
            const m = String(Math.floor(s2sSeconds / 60)).padStart(2, "0");
            const s = String(s2sSeconds % 60).padStart(2, "0");
            s2sMicTimer.textContent = `${m}:${s}`;
          }, 1000);
        }
        drawS2SWaveform();
      } catch (err) {
        if (s2sMicStatus) s2sMicStatus.textContent = `Microphone access denied: ${err.message}`;
      }
    });
  }

  if (btnS2SStop) {
    btnS2SStop.addEventListener("click", () => {
      if (s2sMediaRecorder && s2sMediaRecorder.state === "recording") {
        s2sMediaRecorder.stop();
      }
      btnS2SStop.style.display = "none";
      btnS2SRecord.style.display = "inline-flex";
      if (s2sTimerInterval) clearInterval(s2sTimerInterval);
      if (s2sMicTimer) s2sMicTimer.style.display = "none";
    });
  }

  async function triggerS2STranscription() {
    const reviewBox = document.getElementById("s2s-transcript-review-box");
    const transcriptInput = document.getElementById("s2s-transcript-input");
    const spinner = document.getElementById("s2s-transcribe-spinner");
    const s2sMicStatus = document.getElementById("s2s-mic-status");
    const btnS2SConvert = document.getElementById("btn-s2s-convert");
    const btnRetranscribe = document.getElementById("btn-s2s-retranscribe");

    if (!s2sRecordedBlob) return;

    if (reviewBox) reviewBox.style.display = "block";
    if (spinner) spinner.style.display = "inline";
    if (s2sMicStatus) s2sMicStatus.textContent = "Transcribing your microphone speech locally with Whisper...";
    if (btnS2SConvert) {
      btnS2SConvert.style.display = "inline-flex";
      btnS2SConvert.disabled = true;
      btnS2SConvert.textContent = "Transcribing Words...";
    }

    if (!state.currentOfrendaId) {
      if (s2sMicStatus) s2sMicStatus.textContent = "Please create or select an ofrenda first to transcribe speech.";
      if (btnS2SConvert) {
        btnS2SConvert.disabled = false;
        btnS2SConvert.textContent = "✨ Convert Speech into Memorial Voice";
      }
      return;
    }

    const formData = new FormData();
    formData.append("file", s2sRecordedBlob, "mic_speech.webm");
    const s2sLangSelect = document.getElementById("select-s2s-lang");
    if (s2sLangSelect && s2sLangSelect.value) {
      formData.append("language", s2sLangSelect.value);
    }

    try {
      const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/voice/transcribe-mic`, {
        method: "POST",
        body: formData,
      });
      const data = await parseJsonResponse(res, "Microphone transcription failed");
      if (transcriptInput) {
        transcriptInput.value = data.transcript || "";
      }
      if (s2sMicStatus) {
        if (data.transcript) {
          s2sMicStatus.textContent = "✓ Speech transcribed. You can edit any words above before converting.";
        } else {
          s2sMicStatus.textContent = "⚠️ No speech detected. You can type your spoken words in the text box above.";
        }
      }
      if (btnRetranscribe) btnRetranscribe.style.display = "inline-flex";
    } catch (err) {
      console.warn("Transcription notice:", err);
      if (s2sMicStatus) {
        s2sMicStatus.textContent = `Transcription notice: ${err.message}. You can manually type your message above.`;
      }
      if (btnRetranscribe) btnRetranscribe.style.display = "inline-flex";
    } finally {
      if (spinner) spinner.style.display = "none";
      if (btnS2SConvert) {
        btnS2SConvert.disabled = false;
        btnS2SConvert.textContent = "✨ Convert Speech into Memorial Voice";
      }
    }
  }

  const btnRetranscribe = document.getElementById("btn-s2s-retranscribe");
  if (btnRetranscribe) {
    btnRetranscribe.addEventListener("click", () => {
      triggerS2STranscription();
    });
  }

  // S2S Studio Reference File Selection Listener
  const s2sRefInput = document.getElementById("s2s-ref-file-input");
  const s2sRefStatus = document.getElementById("s2s-ref-file-status");
  const s2sRefPlayer = document.getElementById("s2s-ref-preview-player");
  const s2sRefContainer = document.getElementById("s2s-ref-player-container");

  if (s2sRefInput) {
    s2sRefInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      state.selectedReferenceFile = file;
      if (s2sRefStatus) {
        s2sRefStatus.textContent = `✓ Selected: ${file.name} (${(file.size / 1024).toFixed(0)} KB)`;
        s2sRefStatus.style.color = "var(--success)";
      }
      if (s2sRefPlayer && s2sRefContainer) {
        s2sRefPlayer.src = URL.createObjectURL(file);
        s2sRefContainer.style.display = "block";
      }
      if (elements.voiceRefStatus) {
        elements.voiceRefStatus.textContent = `✓ Selected: ${file.name}`;
        elements.voiceRefStatus.style.color = "var(--success)";
      }
    });
  }

  // S2S Result Card Replay & Download Buttons
  const btnS2SDownload = document.getElementById("btn-s2s-download-voice");
  if (btnS2SDownload) {
    btnS2SDownload.addEventListener("click", () => {
      if (!state.currentOfrendaId) return;
      window.location.href = `/api/ofrendas/${state.currentOfrendaId}/voice/download`;
    });
  }

  const btnS2SReplay = document.getElementById("btn-s2s-replay-voice");
  if (btnS2SReplay) {
    btnS2SReplay.addEventListener("click", () => {
      const player = document.getElementById("s2s-result-audio-player");
      if (player) {
        player.currentTime = 0;
        player.play().catch(() => {});
      }
    });
  }

  if (btnS2SConvert) {
    btnS2SConvert.addEventListener("click", async () => {
      // Prevent duplicate conversion requests while one is running
      if (state.isConvertingVoice) {
        console.warn("A voice conversion request is already running.");
        return;
      }

      if (!state.currentOfrendaId) {
        const ok = await saveStep1();
        if (!ok || !state.currentOfrendaId) {
          alert("Please enter a name for the ofrenda first.");
          return;
        }
      }
      if (!elements.checkVoiceConsent.checked) {
        alert("Affirmative family permission is strictly required for memorial voice recreation.");
        elements.checkVoiceConsent.focus();
        return;
      }
      const authBy = elements.inputVoiceAuth.value.trim();
      if (!authBy) {
        alert("Please enter the authorizing family member's name.");
        elements.inputVoiceAuth.focus();
        return;
      }
      if (!s2sRecordedBlob) {
        alert("Please record your microphone speech first.");
        return;
      }

      state.isConvertingVoice = true;
      btnS2SConvert.disabled = true;
      btnS2SConvert.textContent = "⏳ Converting Speech...";

      const progressBar = document.getElementById("s2s-conversion-progress");
      const progressText = document.getElementById("s2s-conversion-progress-text");
      if (progressBar) progressBar.style.display = "block";
      if (progressText) progressText.textContent = "Phase 1/2: Synthesizing natural base speech with Kokoro-82M...";

      const stageTimer = setTimeout(() => {
        if (progressText) progressText.textContent = "Phase 2/2: Transferring reference vocal timbre with OpenVoice V2...";
      }, 7000);

      const loadingMsg = document.getElementById("voice-loading-message");
      if (loadingMsg) loadingMsg.textContent = "Running neural voice conversion into memorial voice...";
      if (elements.voiceLoading) elements.voiceLoading.style.display = "block";

      const formData = new FormData();
      formData.append("file", s2sRecordedBlob, "mic_speech.webm");
      formData.append("authorized_by", authBy);
      formData.append("confirmed_permission", "true");

      const s2sLangSelect = document.getElementById("select-s2s-lang");
      if (s2sLangSelect && s2sLangSelect.value) {
        formData.append("language", s2sLangSelect.value);
      }

      const transcriptInput = document.getElementById("s2s-transcript-input");
      const reviewedText = transcriptInput ? transcriptInput.value.trim() : "";
      if (reviewedText) {
        formData.append("transcript", reviewedText);
      }

      const s2sEngineSelect = document.getElementById("select-s2s-engine");
      if (s2sEngineSelect && s2sEngineSelect.value) {
        formData.append("engine", s2sEngineSelect.value);
      }

      if (state.selectedReferenceFile) {
        formData.append("reference_file", state.selectedReferenceFile);
      }

      try {
        const res = await fetch(`/api/ofrendas/${state.currentOfrendaId}/voice/convert`, {
          method: "POST",
          body: formData,
        });

        const data = await parseJsonResponse(res, "Voice conversion failed");

        if (data.status === "unavailable") {
          alert("Voice Conversion Notice: " + data.message);
          if (s2sMicStatus) s2sMicStatus.textContent = `Conversion setup notice: ${data.message}`;
        } else {
          const expNote = data.experimental_hindi ? " (Experimental Hindi)" : "";
          if (s2sMicStatus) s2sMicStatus.textContent = `✓ Converted speech into memorial voice successfully (${(data.duration_s || 0).toFixed(1)}s)!${expNote}`;

          const audioUrl = `/api/ofrendas/${state.currentOfrendaId}/voice/audio?t=${Date.now()}`;

          // Update Studio Result Card
          const s2sResultCard = document.getElementById("s2s-result-card");
          const s2sResultPlayer = document.getElementById("s2s-result-audio-player");
          const s2sEngineBadge = document.getElementById("s2s-result-engine-badge");
          const s2sDurationInfo = document.getElementById("s2s-result-duration-info");

          if (s2sResultCard) s2sResultCard.style.display = "block";
          if (s2sResultPlayer) {
            s2sResultPlayer.src = audioUrl;
            s2sResultPlayer.play().catch(() => {});
          }
          if (s2sEngineBadge) s2sEngineBadge.textContent = `${data.engine_used || 'Kokoro + OpenVoice'}${expNote}`;
          if (s2sDurationInfo) s2sDurationInfo.textContent = `Duration: ${(data.duration_s || 0).toFixed(1)}s`;

          // Synchronize Top-Level Voice Result Box
          if (elements.voiceResultBox) elements.voiceResultBox.style.display = "block";
          if (elements.voiceAudioPlayer) {
            elements.voiceAudioPlayer.src = audioUrl;
          }
          if (elements.voiceDurationInfo && data.duration_s) {
            elements.voiceDurationInfo.textContent = `Duration: ${data.duration_s.toFixed(1)}s • Engine: ${data.engine_used || 'Kokoro + OpenVoice'}${expNote}`;
          }
          if (s2sResultCard) {
            s2sResultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
          updatePreviewIframe();
        }
      } catch (err) {
        alert("Voice Conversion Notice: " + err.message);
        if (s2sMicStatus) s2sMicStatus.textContent = `Error: ${err.message}`;
      } finally {
        clearTimeout(stageTimer);
        state.isConvertingVoice = false;
        btnS2SConvert.disabled = false;
        btnS2SConvert.textContent = "✨ Convert Speech into Memorial Voice";
        if (progressBar) progressBar.style.display = "none";
        if (elements.voiceLoading) elements.voiceLoading.style.display = "none";
      }
    });
  }

  // Atmospheric Sound Interactions
  document.addEventListener("click", (e) => {
    if (e.target.closest("button") || e.target.closest(".btn")) {
      if (window.OfrendaAudio) window.OfrendaAudio.playButtonClick();
    }
  });

  let typeThrottle = 0;
  const onTypeKey = () => {
    const now = Date.now();
    if (now - typeThrottle > 90) {
      typeThrottle = now;
      if (window.OfrendaAudio) window.OfrendaAudio.playTypeSound();
    }
  };
  if (elements.textareaStory) elements.textareaStory.addEventListener("keydown", onTypeKey);
  if (elements.textareaRemembrance) elements.textareaRemembrance.addEventListener("keydown", onTypeKey);

  // Language switcher
  elements.btnLangToggle.addEventListener("click", () => {
    const newLang = state.language === "es" ? "en" : "es";
    setLanguage(newLang);
  });
  elements.selectLang.addEventListener("change", (e) => {
    setLanguage(e.target.value);
  });

  // Step 1
  elements.btnNext1.addEventListener("click", async () => {
    const ok = await saveStep1();
    if (ok) goToStep(2);
  });

  // Step 2 Chip Inputs
  elements.btnAddFood.addEventListener("click", () => addChip(elements.inputFood, elements.chipsFoods, state.foods, 12));
  elements.inputFood.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); addChip(elements.inputFood, elements.chipsFoods, state.foods, 12); }
  });

  elements.btnAddDrink.addEventListener("click", () => addChip(elements.inputDrink, elements.chipsDrinks, state.drinks, 6));
  elements.inputDrink.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); addChip(elements.inputDrink, elements.chipsDrinks, state.drinks, 6); }
  });

  elements.btnAddSong.addEventListener("click", () => addChip(elements.inputSong, elements.chipsSongs, state.songs, 6));
  elements.inputSong.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); addChip(elements.inputSong, elements.chipsSongs, state.songs, 6); }
  });

  elements.btnAddObject.addEventListener("click", () => addChip(elements.inputObject, elements.chipsObjects, state.objects, 8));
  elements.inputObject.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); addChip(elements.inputObject, elements.chipsObjects, state.objects, 8); }
  });

  elements.btnBack2.addEventListener("click", () => goToStep(1));
  elements.btnNext2.addEventListener("click", async () => {
    const ok = await saveStep2();
    if (ok) goToStep(3);
  });

  // Step 3
  elements.inputPhoto.addEventListener("change", handlePhotoSelected);
  elements.btnRecord.addEventListener("click", startRecording);
  elements.btnStopRecord.addEventListener("click", stopRecording);

  elements.btnBack3.addEventListener("click", () => goToStep(2));
  elements.btnNext3.addEventListener("click", async () => {
    const ok = await saveStep3();
    if (ok) {
      goToStep(4);
      updatePreviewIframe();
      if (!elements.textareaRemembrance.value.trim()) {
        generateRemembrance();
      }
    }
  });

  // Step 4 Actions
  elements.btnGenerate.addEventListener("click", generateRemembrance);
  elements.btnRegenerate.addEventListener("click", generateRemembrance);
  elements.btnSaveRemembrance.addEventListener("click", saveRemembranceEdits);

  // Step 4 Voice Recreation
  elements.inputVoiceRef.addEventListener("change", handleVoiceRefSelected);
  elements.btnUseStep3Audio.addEventListener("click", handleUseStep3Audio);
  elements.btnSynthesizeVoice.addEventListener("click", synthesizeVoice);
  elements.btnDownloadVoice.addEventListener("click", downloadSynthesizedVoice);
  elements.btnDeleteVoice.addEventListener("click", deleteVoice);

  elements.btnDownloadHtml.addEventListener("click", () => {
    if (state.currentOfrendaId) {
      window.location.href = `/api/ofrendas/${state.currentOfrendaId}/download`;
    }
  });

  elements.btnPrintPdf.addEventListener("click", () => {
    if (elements.previewIframe && elements.previewIframe.contentWindow) {
      elements.previewIframe.contentWindow.focus();
      elements.previewIframe.contentWindow.print();
    }
  });

  elements.btnBack4.addEventListener("click", () => goToStep(3));
  elements.btnStartNew.addEventListener("click", resetWizard);

  // Drawer
  elements.btnOpenDrawer.addEventListener("click", () => {
    loadSavedOfrendas();
    elements.drawerBackdrop.classList.add("active");
  });
  elements.btnCloseDrawer.addEventListener("click", () => {
    elements.drawerBackdrop.classList.remove("active");
  });
  elements.btnNewFromDrawer.addEventListener("click", () => {
    elements.drawerBackdrop.classList.remove("active");
    resetWizard();
  });

  // Hackathon UI & 3D Interactive Features
  if (elements.btnDemoQuick) {
    elements.btnDemoQuick.addEventListener("click", loadDemoOfrenda);
  }
  if (elements.btnAmbientToggle) {
    elements.btnAmbientToggle.addEventListener("click", toggleAmbient);
  }
  if (elements.btnFullscreenPreview) {
    elements.btnFullscreenPreview.addEventListener("click", () => toggleFullscreenAltar(true));
  }
  if (elements.btnCloseFullscreen) {
    elements.btnCloseFullscreen.addEventListener("click", () => toggleFullscreenAltar(false));
  }
  initSuggestionPills();

  if (elements.voiceAudioPlayer) {
    elements.voiceAudioPlayer.addEventListener("play", startVoiceSpectrumVisualizer);
    elements.voiceAudioPlayer.addEventListener("pause", stopVoiceSpectrumVisualizer);
    elements.voiceAudioPlayer.addEventListener("ended", stopVoiceSpectrumVisualizer);
  }
}

// Initial Boot
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  setLanguage("es");
  checkHealth();
  setInterval(checkHealth, 10000);
});
