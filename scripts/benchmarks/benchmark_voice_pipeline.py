"""Generic Benchmark for Complete Voice Pipeline (Whisper -> Kokoro -> OpenVoice).

Measures:
1. Stage 1: Whisper ASR transcription latency & accuracy.
2. Stage 2: Kokoro-82M text-to-speech synthesis latency & RTF.
3. Stage 3: OpenVoice V2 ToneColorConverter tone transfer latency & RTF.
4. Total end-to-end pipeline latency and peak RAM usage on CPU.

Uses repository fixtures (tests/fixtures/sample_en.wav) by default.
No personal data, reference memorials, or private audio are required.
Outputs are saved to gitignored directories.
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
sys.path.insert(0, str(root_dir / "tmp_seed_vc"))

import numpy as np
import psutil
import soundfile as sf
import torch
from faster_whisper import WhisperModel
from huggingface_hub import hf_hub_download
from kokoro import KModel, KPipeline
from modules.openvoice.api import ToneColorConverter


def get_current_ram_gb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / (1024**3)


def run_pipeline_benchmark(reference_wav: Path, output_dir: Path, device: str = "cpu"):
    print("=" * 70)
    print("END-TO-END VOICE PIPELINE CPU BENCHMARK")
    print("Pipeline: Whisper ASR -> Kokoro TTS -> OpenVoice ToneColorConverter")
    print("=" * 70)

    if not reference_wav.exists():
        print(f"[ERROR] Reference WAV not found at: {reference_wav}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    ram_baseline = get_current_ram_gb()
    max_ram = ram_baseline
    print(f"System Baseline RAM: {ram_baseline:.2f} GB")

    # 1. Load Models
    print("\n--- 1. LOADING ENGINE MODULES ---")
    t0_init = time.perf_counter()

    whisper = WhisperModel("base", device="cpu", compute_type="int8")
    kmodel = KModel(repo_id="hexgrad/Kokoro-82M").to(device).eval()

    ov_config_path = hf_hub_download(repo_id="myshell-ai/OpenVoiceV2", filename="converter/config.json")
    ov_ckpt_path = hf_hub_download(repo_id="myshell-ai/OpenVoiceV2", filename="converter/checkpoint.pth")
    converter = ToneColorConverter(config_path=ov_config_path, device=device)
    converter.load_ckpt(ov_ckpt_path)

    t_init = time.perf_counter() - t0_init
    cur_ram = get_current_ram_gb()
    max_ram = max(max_ram, cur_ram)
    print(f"[OK] All engines loaded in {t_init:.2f}s | Current RAM: {cur_ram:.2f} GB")

    # Extract target reference speaker embedding
    print(f"\n--- 2. EXTRACTING REFERENCE SPEAKER EMBEDDING ---")
    print(f"Reference Audio: {reference_wav}")
    t0_embed = time.perf_counter()
    target_se, _ = converter.extract_se([str(reference_wav)])
    t_embed = time.perf_counter() - t0_embed
    print(f"[OK] Speaker embedding extracted in {t_embed:.2f}s")

    # Test Scenarios
    scenarios = [
        {
            "lang": "en",
            "lang_code": "a",
            "voice": "af_heart",
            "text": "In loving memory, you will always be cherished and remembered.",
        },
        {
            "lang": "hi",
            "lang_code": "h",
            "voice": "hf_alpha",
            "text": "हम आपको हमेशा याद रखेंगे। आपकी सीख सदैव हमारा मार्गदर्शन करेगी।",
        },
    ]

    print("\n--- 3. EXECUTING BENCHMARK RUNS ---")
    results = []

    for sc in scenarios:
        lang = sc["lang"]
        lang_code = sc["lang_code"]
        voice = sc["voice"]
        text = sc["text"]

        print(f"\n>>> Running Scenario: {lang.upper()} ({voice})")
        t_start_e2e = time.perf_counter()

        # Stage A: Kokoro TTS Synthesis
        t0_tts = time.perf_counter()
        pipeline = KPipeline(lang_code=lang_code, model=kmodel)
        chunks = []
        for gs, ps, audio in pipeline(text, voice=voice, speed=1.0):
            if audio is not None:
                chunks.append(audio)
        t_tts = time.perf_counter() - t0_tts

        raw_audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
        raw_tts_path = output_dir / f"stage2_raw_{lang}_{voice}.wav"
        sf.write(str(raw_tts_path), raw_audio, 24000, subtype="PCM_16")

        info_raw = sf.info(str(raw_tts_path))
        rtf_tts = t_tts / info_raw.duration if info_raw.duration > 0 else 0.0

        cur_ram = get_current_ram_gb()
        max_ram = max(max_ram, cur_ram)

        # Stage B: OpenVoice Tone Transfer
        t0_vc = time.perf_counter()
        source_se, _ = converter.extract_se([str(raw_tts_path)])
        converted_path = output_dir / f"stage3_converted_{lang}_{voice}.wav"

        converter.convert(
            audio_src_path=str(raw_tts_path),
            src_se=source_se,
            tgt_se=target_se,
            output_path=str(converted_path),
            message="@OfrendaKeeper",
        )
        t_vc = time.perf_counter() - t0_vc
        info_conv = sf.info(str(converted_path))
        rtf_vc = t_vc / info_conv.duration if info_conv.duration > 0 else 0.0

        cur_ram = get_current_ram_gb()
        max_ram = max(max_ram, cur_ram)

        # Stage C: Whisper Verification of converted audio
        t0_asr = time.perf_counter()
        w_segs, w_info = whisper.transcribe(
            str(converted_path),
            language=lang,
            initial_prompt="नमस्ते" if lang == "hi" else None,
            beam_size=5,
        )
        transcript = " ".join([s.text for s in w_segs]).strip()
        t_asr = time.perf_counter() - t0_asr

        t_total = time.perf_counter() - t_start_e2e
        total_rtf = (t_tts + t_vc) / info_conv.duration if info_conv.duration > 0 else 0.0

        print(f"  Stage 1 (TTS Generation):       {t_tts:.2f}s (Audio: {info_raw.duration:.2f}s | RTF: {rtf_tts:.2f}x)")
        print(f"  Stage 2 (Tone Color Transfer):  {t_vc:.2f}s (Audio: {info_conv.duration:.2f}s | RTF: {rtf_vc:.2f}x)")
        print(f"  Stage 3 (Whisper Verification): {t_asr:.2f}s")
        print(f"  Total Pipeline Latency:         {t_total:.2f}s (Combined Synthesis RTF: {total_rtf:.2f}x)")
        print(f"  Intelligibility Transcript:     \"{transcript}\"")

        results.append({
            "lang": lang,
            "tts_time": t_tts,
            "vc_time": t_vc,
            "total_time": t_total,
            "duration": info_conv.duration,
            "rtf": total_rtf,
            "transcript": transcript,
        })

    print("\n" + "=" * 70)
    print(f"PIPELINE BENCHMARK COMPLETE")
    print(f"Peak RAM Usage: {max_ram:.2f} GB (Delta: +{max_ram - ram_baseline:.2f} GB)")
    print(f"Artifacts saved in: {output_dir}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="End-to-End Voice Pipeline Benchmark")
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("tests/fixtures/sample_en.wav"),
        help="Path to reference speaker WAV (default: tests/fixtures/sample_en.wav)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/benchmarks/pipeline"),
        help="Directory to save output WAVs (default: data/benchmarks/pipeline)",
    )
    parser.add_argument("--device", default="cpu", help="Computation device (default: cpu)")
    args = parser.parse_args()

    run_pipeline_benchmark(
        reference_wav=args.reference,
        output_dir=args.output_dir,
        device=args.device,
    )


if __name__ == "__main__":
    main()

