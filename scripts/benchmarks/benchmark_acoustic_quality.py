"""Generic Acoustic Analysis and Quality Benchmark Tool.

Computes:
1. Signal properties: Duration, sample rate, channels, bit depth.
2. Energy: RMS amplitude, peak amplitude, digital clipping.
3. Pitch (F0): Mean pitch (Hz), pitch standard deviation (Hz), pitch variance.
4. Timbre & Brightness: Spectral centroid (Hz), spectral flatness, zero-crossing rate.
5. Intelligibility: Whisper ASR transcription, detected language, confidence.

Usage:
    python scripts/benchmarks/benchmark_acoustic_quality.py --audio path/to/audio.wav
    python scripts/benchmarks/benchmark_acoustic_quality.py --compare file1.wav file2.wav
"""

import argparse
import os
import sys
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
import soundfile as sf
from faster_whisper import WhisperModel


def analyze_file(path: Path, whisper_model: WhisperModel = None) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    info = sf.info(str(path))
    data, sr = sf.read(str(path), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)

    rms = float(np.sqrt(np.mean(data**2)))
    peak = float(np.max(np.abs(data)))
    clipping = bool(peak >= 0.999)

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
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y=data)))

    transcript = ""
    lang = ""
    prob = 0.0
    if whisper_model is not None:
        try:
            segments, t_info = whisper_model.transcribe(str(path), beam_size=5)
            transcript = " ".join([s.text for s in segments]).strip()
            lang = t_info.language
            prob = t_info.language_probability
        except Exception as e:
            transcript = f"[Transcription Error: {e}]"

    return {
        "file": path.name,
        "path": str(path),
        "duration": info.duration,
        "sample_rate": info.samplerate,
        "channels": info.channels,
        "format": f"{info.format} ({info.subtype})",
        "rms": rms,
        "peak": peak,
        "clipped": clipping,
        "mean_f0": mean_f0,
        "std_f0": std_f0,
        "cv_f0": cv_f0,
        "spectral_centroid": sc,
        "spectral_flatness": flatness,
        "zcr": zcr,
        "transcript": transcript,
        "detected_lang": lang,
        "lang_prob": prob,
    }


def print_stats(stats: dict, label: str = ""):
    header = f"=== {label or stats['file']} ==="
    print(header)
    print(f"  Path:               {stats['path']}")
    print(f"  Duration:           {stats['duration']:.2f} s | {stats['sample_rate']} Hz | {stats['format']}")
    print(f"  RMS Amplitude:      {stats['rms']:.4f} | Peak Amplitude: {stats['peak']:.4f} (Clipping: {stats['clipped']})")
    print(f"  Mean Pitch (F0):    {stats['mean_f0']:.1f} Hz (StdDev: {stats['std_f0']:.1f} Hz, CV: {stats['cv_f0']:.1f}%)")
    print(f"  Spectral Centroid:  {stats['spectral_centroid']:.1f} Hz (Brightness)")
    print(f"  Spectral Flatness:  {stats['spectral_flatness']:.6f} | Zero-Crossing Rate: {stats['zcr']:.4f}")
    if stats["transcript"]:
        print(f"  Whisper Transcript: \"{stats['transcript']}\" (Lang: {stats['detected_lang']}, Conf: {stats['lang_prob']:.2f})")
    print()


def main():
    parser = argparse.ArgumentParser(description="Generic Audio Acoustic Quality Benchmark")
    parser.add_argument("--audio", type=Path, default=Path("tests/fixtures/sample_en.wav"), help="Audio file to analyze")
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("FILE1", "FILE2"), help="Compare two audio files")
    parser.add_argument("--no-asr", action="store_true", help="Skip Whisper ASR transcription")
    args = parser.parse_args()

    whisper = None
    if not args.no_asr:
        print("Loading Whisper base for transcription...")
        whisper = WhisperModel("base", device="cpu", compute_type="int8")

    if args.compare:
        f1, f2 = args.compare
        s1 = analyze_file(f1, whisper)
        s2 = analyze_file(f2, whisper)
        print("\n" + "=" * 60)
        print("ACOUSTIC COMPARISON REPORT")
        print("=" * 60)
        print_stats(s1, f"FILE 1: {f1.name}")
        print_stats(s2, f"FILE 2: {f2.name}")
        print("--- DIFFERENTIAL SUMMARY ---")
        print(f"  Duration Delta:          {s2['duration'] - s1['duration']:+.2f} s")
        print(f"  Mean Pitch Delta:        {s2['mean_f0'] - s1['mean_f0']:+.1f} Hz")
        print(f"  Spectral Centroid Delta: {s2['spectral_centroid'] - s1['spectral_centroid']:+.1f} Hz")
    else:
        stats = analyze_file(args.audio, whisper)
        print_stats(stats)


if __name__ == "__main__":
    main()

