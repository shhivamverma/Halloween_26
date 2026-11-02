# Voice Pipeline Benchmarking Suite

This directory contains standalone, reproducible benchmark utilities for evaluating the offline voice synthesis and conversion components of **Offline Ofrenda Keeper** on CPU hardware.

None of these scripts require personal memorial data, user voice recordings, or proprietary cloud APIs. All benchmarks use open-source weights and repository test fixtures (or generic synthetic test sentences).

---

## 1. Available Benchmarks

### A. Kokoro-82M TTS CPU Benchmark (`benchmark_kokoro.py`)
Measures standalone Kokoro-82M speech generation speed, real-time factor (RTF), memory overhead, and speech intelligibility for English and Hindi.

```bash
# Run on CPU with default settings
python scripts/benchmarks/benchmark_kokoro.py

# Custom output directory
python scripts/benchmarks/benchmark_kokoro.py --output-dir data/my_kokoro_benchmarks
```

**Metrics Evaluated:**
- **Latency & RTF:** Processing time divided by generated audio duration (lower is faster; $<1.0\times$ indicates faster than real time).
- **RAM Overhead:** Measured before and after model allocation via `psutil`.
- **Acoustic Profiling:** Pitch (F0) mean, pitch variation (CV%), and spectral centroid.
- **Whisper Pronunciation Check:** Re-transcribes synthesized speech via `faster-whisper` (base, int8) to verify phonetic intelligibility.

---

### B. End-to-End Voice Pipeline Benchmark (`benchmark_voice_pipeline.py`)
Evaluates the full offline voice recreation sequence:
$$\text{Input Speech} \xrightarrow{\text{Whisper ASR}} \text{Editable Text} \xrightarrow{\text{Kokoro-82M TTS}} \text{Base Speech} \xrightarrow{\text{OpenVoice V2 VC}} \text{Target Timbre}$$

```bash
# Run pipeline benchmark using the repository test fixture
python scripts/benchmarks/benchmark_voice_pipeline.py

# Benchmark with a custom reference audio sample
python scripts/benchmarks/benchmark_voice_pipeline.py --reference path/to/reference_sample.wav
```

**Metrics Evaluated:**
- **Stage 1 (TTS Generation):** Kokoro synthesis latency and RTF.
- **Stage 2 (Tone Color Converter):** OpenVoice tone color embedding extraction and conversion latency.
- **Combined Pipeline Latency:** Total wall-clock time from text prompt to final personalized WAV.
- **Peak RAM Delta:** Maximum system memory consumed by all active PyTorch models in memory.

---

### C. Acoustic Quality & Comparison Analyzer (`benchmark_acoustic_quality.py`)
CLI utility for analyzing any WAV file's signal fidelity, acoustic properties, and intelligibility.

```bash
# Analyze a single audio file (defaults to tests/fixtures/sample_en.wav)
python scripts/benchmarks/benchmark_acoustic_quality.py --audio tests/fixtures/sample_en.wav

# Compare two audio files side-by-side (e.g. source vs. converted)
python scripts/benchmarks/benchmark_acoustic_quality.py --compare source.wav converted.wav
```

**Metrics Evaluated:**
- Signal amplitude, RMS energy, and digital clipping check ($\ge 0.999$).
- Pitch (F0) tracking via probabilistic YIN (`librosa.pyin`).
- Spectral centroid (timbre brightness) and spectral flatness.
- Whisper ASR transcript, detected language, and confidence score.

---

## 2. Typical Hardware Reference Numbers (x86_64 CPU)

| Metric | Kokoro TTS (CPU) | OpenVoice V2 VC (CPU) | Full Pipeline (CPU) |
| :--- | :---: | :---: | :---: |
| **English RTF** | ~0.15–0.30× | ~0.20–0.40× | ~0.35–0.70× |
| **Hindi RTF** | ~0.25–0.45× | ~0.25–0.45× | ~0.50–0.90× |
| **Process RAM Peak** | ~800 MB | ~1.4 GB | ~1.6 GB |
| **Total System RAM** | 8 GB Min / 16 GB Rec | 8 GB Min / 16 GB Rec | 8 GB Min / 16 GB Rec |

---

## 3. Privacy & Output Isolation

All generated audio files from these benchmark scripts are written to directories under `data/benchmarks/`, which are strictly excluded from Git tracking via `.gitignore`. No synthetic speech or benchmark outputs will ever be committed to the repository.

