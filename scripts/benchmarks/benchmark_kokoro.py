"""Generic Benchmark for Kokoro-82M TTS on CPU.

Evaluates Kokoro-82M performance across English and Hindi:
1. Generation latency (seconds) and Real-Time Factor (RTF).
2. Peak RAM consumption (GB) via psutil.
3. Acoustic expressiveness (Mean F0 pitch, F0 variance, spectral centroid).
4. Pronunciation intelligibility verification via Whisper transcription.

All output WAV files are written to a gitignored output directory.
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Project root
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

import librosa
import numpy as np
import psutil
import soundfile as sf
import torch
from faster_whisper import WhisperModel
from kokoro import KModel, KPipeline


def get_current_ram_gb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / (1024**3)


def analyze_audio(path: Path) -> dict:
    info = sf.info(str(path))
    data, sr = sf.read(str(path), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)

    rms = float(np.sqrt(np.mean(data**2)))
    peak = float(np.max(np.abs(data)))

    try:
        f0, _, _ = librosa.pyin(
            data,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
        )
        f0_clean = f0[~np.isnan(f0)]
        mean_f0 = float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0.0
        std_f0 = float(np.std(f0_clean)) if len(f0_clean) > 0 else 0.0
        cv_f0 = (std_f0 / mean_f0 * 100.0) if mean_f0 > 0 else 0.0
    except Exception:
        mean_f0, std_f0, cv_f0 = 0.0, 0.0, 0.0

    sc = float(np.mean(librosa.feature.spectral_centroid(y=data, sr=sr)))
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=data)))

    return {
        "duration": info.duration,
        "sample_rate": info.samplerate,
        "rms": rms,
        "peak": peak,
        "mean_f0": mean_f0,
        "std_f0": std_f0,
        "cv_f0": cv_f0,
        "spectral_centroid": sc,
        "flatness": flatness,
    }


def run_benchmark(output_dir: Path, device: str = "cpu"):
    print("=" * 70)
    print("KOKORO-82M TTS CPU PERFORMANCE BENCHMARK")
    print("=" * 70)

    output_dir.mkdir(parents=True, exist_ok=True)
    ram_start = get_current_ram_gb()
    max_ram = ram_start

    print(f"\n[1/3] Loading Kokoro-82M on {device}...")
    t0_load = time.perf_counter()
    kmodel = KModel(repo_id="hexgrad/Kokoro-82M").to(device).eval()
    t_load = time.perf_counter() - t0_load
    print(f"      Kokoro loaded in {t_load:.2f}s | RAM: {get_current_ram_gb():.2f} GB")

    print("\n[2/3] Loading Whisper for intelligibility check...")
    whisper = WhisperModel("base", device="cpu", compute_type="int8")
    print(f"      Whisper base loaded | RAM: {get_current_ram_gb():.2f} GB")

    test_cases = [
        {
            "lang_name": "English",
            "lang_code": "a",
            "text": "In loving memory, you will forever remain in our hearts.",
            "voices": [
                {"id": "af_heart", "label": "Female (Heart)"},
                {"id": "am_adam", "label": "Male (Adam)"},
            ],
        },
        {
            "lang_name": "Hindi",
            "lang_code": "h",
            "text": "हम आपको हमेशा याद रखेंगे। आपकी यादें हमारे दिलों में जीवित हैं।",
            "voices": [
                {"id": "hf_alpha", "label": "Female (Alpha - Native)"},
                {"id": "hm_omega", "label": "Male (Omega - Native)"},
            ],
        },
    ]

    print("\n[3/3] Running synthesis benchmarks...")
    for tc in test_cases:
        lang_name = tc["lang_name"]
        lang_code = tc["lang_code"]
        text = tc["text"]

        pipeline = KPipeline(lang_code=lang_code, model=kmodel)

        print(f"\n--- Language: {lang_name} ({lang_code}) ---")
        print(f"Input text: \"{text}\"")

        for v in tc["voices"]:
            voice_id = v["id"]
            voice_label = v["label"]
            out_file = output_dir / f"kokoro_{lang_name.lower()}_{voice_id}.wav"

            t0_gen = time.perf_counter()
            chunks = []
            for gs, ps, audio in pipeline(text, voice=voice_id, speed=1.0):
                if audio is not None:
                    chunks.append(audio)
            t_gen = time.perf_counter() - t0_gen

            if not chunks:
                print(f"  [ERROR] No audio produced for {voice_id}")
                continue

            audio_arr = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
            sf.write(str(out_file), audio_arr, 24000, subtype="PCM_16")

            cur_ram = get_current_ram_gb()
            max_ram = max(max_ram, cur_ram)

            stats = analyze_audio(out_file)
            rtf = t_gen / stats["duration"] if stats["duration"] > 0 else 0.0

            # Transcribe back
            w_segs, _ = whisper.transcribe(
                str(out_file),
                language="hi" if lang_code == "h" else "en",
                initial_prompt="नमस्ते" if lang_code == "h" else None,
                beam_size=5,
            )
            retranscribed = " ".join([s.text for s in w_segs]).strip()

            print(f"  Voice: {voice_id} ({voice_label})")
            print(f"    Latency: {t_gen:.2f}s | Audio: {stats['duration']:.2f}s | RTF: {rtf:.2f}x")
            print(f"    F0 Pitch: {stats['mean_f0']:.1f} Hz (StdDev: {stats['std_f0']:.1f} Hz)")
            print(f"    Spectral Centroid: {stats['spectral_centroid']:.1f} Hz")
            print(f"    Whisper Transcription: \"{retranscribed}\"")

    print("\n" + "=" * 70)
    print(f"BENCHMARK COMPLETE | Peak RAM: {max_ram:.2f} GB")
    print(f"Audio outputs written to: {output_dir}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Kokoro-82M TTS CPU Benchmark")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/benchmarks/kokoro"),
        help="Directory to save generated test WAVs (default: data/benchmarks/kokoro)",
    )
    parser.add_argument("--device", default="cpu", help="Computation device (default: cpu)")
    args = parser.parse_args()

    run_benchmark(output_dir=args.output_dir, device=args.device)


if __name__ == "__main__":
    main()

