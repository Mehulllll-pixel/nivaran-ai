"""
regression_test_audio.py
========================
Runs recording2.mp4 and recording3.mp4 back-to-back through the full pipeline:
  FFmpeg → Whisper → extract_intent_and_promise() → determine_recovery_action()

Do NOT pre-clean or correct Whisper transcripts before sending to Groq.
Run in the terminal where GROQ_API_KEY is set.
"""
import datetime
import json
import subprocess
import time

import numpy as np
import torch
from transformers import pipeline as hf_pipeline

from extraction import extract_intent_and_promise
from guardrails import determine_recovery_action

CALL_DATE = datetime.datetime(2026, 8, 22, 12, 0, 0)
MODEL_ID  = "Oriserve/Whisper-Hindi2Hinglish-Swift"
DIVIDER   = "=" * 60

AUDIO_FILES = [
    "audio/recording2.mp4",
    "audio/recording3.mp4",
]


def read_audio_with_ffmpeg(file_path: str) -> np.ndarray:
    """Verbatim copy from whisper_test.py — do NOT import that file."""
    command = [
        "ffmpeg", "-i", file_path,
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ar", "16000", "-ac", "1", "-y", "-"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed (exit {process.returncode}):\n"
            f"{stderr.decode('utf-8', errors='ignore')}"
        )
    return np.frombuffer(stdout, dtype=np.float32)


# ── Load Whisper once ─────────────────────────────────────────────────────────
if torch.cuda.is_available():
    device, torch_dtype = "cuda:0", torch.float16
    print("Hardware: CUDA GPU (float16)")
else:
    device, torch_dtype = "cpu", torch.float32
    print("Hardware: CPU (float32)")

print(f"Loading Whisper model '{MODEL_ID}'...")
t0 = time.time()
asr_pipe = hf_pipeline(
    "automatic-speech-recognition",
    model=MODEL_ID,
    torch_dtype=torch_dtype,
    device=device
)
print(f"Model loaded in {time.time() - t0:.1f}s\n")

# ── Process each file ─────────────────────────────────────────────────────────
for audio_file in AUDIO_FILES:
    label = audio_file.split("/")[-1]
    print(DIVIDER)
    print(f"{label.upper()} — REAL AUDIO TEST")
    print(DIVIDER)
    print(f"Audio file : {audio_file}")
    print(f"Call date  : {CALL_DATE.date()}")
    print()

    whisper_ok = False
    transcript = ""
    result = None
    action = None

    # Step 1 — FFmpeg + Whisper
    try:
        t1 = time.time()
        audio_data = read_audio_with_ffmpeg(audio_file)
        ffmpeg_dur = time.time() - t1

        t2 = time.time()
        asr_result = asr_pipe({"raw": audio_data, "sampling_rate": 16000})
        whisper_dur = time.time() - t2

        transcript = asr_result.get("text", "").strip()
        whisper_ok = True
        print(f"FFmpeg: {ffmpeg_dur:.2f}s  |  Whisper: {whisper_dur:.2f}s")
    except Exception as e:
        print(f"[FAIL] Whisper: {e}")

    print()
    print("Raw Whisper transcript:")
    print(transcript if transcript else "[EMPTY]")
    print()

    # Step 2 — Groq extraction (raw transcript, no cleanup)
    groq_ok = False
    extraction_valid = False
    if whisper_ok and transcript:
        try:
            result = extract_intent_and_promise(transcript, CALL_DATE)
            groq_ok = not result["fallback_mode"]
            ext = result["extraction"]
            extraction_valid = {"intent","sentiment","promised_amount","temporal",
                                "confidence","reasoning"}.issubset(ext.keys())

            print("RAW GROQ RESPONSE:")
            print(result["raw_response"])
            print()
            print("PARSED EXTRACTION:")
            print(json.dumps(ext, indent=2, default=str))
            print()
            print(f"PYTHON RESOLVED DATE:")
            print(result["resolved_promised_date"])
            print()
        except Exception as e:
            print(f"[FAIL] Groq extraction: {e}")
    else:
        print("[SKIP] Groq — no valid transcript.")

    # Step 3 — Guardrails
    guardrail_ok = False
    if result is not None:
        try:
            action = determine_recovery_action(result)
            guardrail_ok = True
            print("GUARDRAIL / RECOVERY ACTION:")
            print(json.dumps(action, indent=2, default=str))
            print()
        except Exception as e:
            print(f"[FAIL] Guardrail: {e}")

    # Step 4 — Diagnostic report
    print(DIVIDER)
    print(f"DIAGNOSTIC REPORT — {label}")
    print(DIVIDER)
    print(f"  Whisper succeeded         : {'YES' if whisper_ok else 'NO'}")
    print(f"  Groq strict json_schema   : {'SUCCEEDED' if groq_ok else 'FALLBACK/FAILED'}")
    print(f"  Extraction structure valid: {'YES' if extraction_valid else 'NO'}")
    if result is not None:
        ext = result["extraction"]
        print(f"  Intent                    : {ext.get('intent')}")
        print(f"  Temporal type             : {ext.get('temporal', {}).get('type')}")
        print(f"  event_trigger             : {ext.get('temporal', {}).get('event_trigger')}")
        print(f"  Resolved date             : {result['resolved_promised_date']}")
    if action is not None:
        print(f"  Action                    : {action.get('action')}")
        print(f"  compliance_block          : {action.get('compliance_block')}")
        print(f"  escalate_to_human         : {action.get('escalate_to_human')}")
        print(f"  reconciliation_required   : {action.get('reconciliation_required')}")
        print(f"  generic_follow_up         : {action.get('generic_follow_up')}")
        print(f"  follow_up_delay_days      : {action.get('follow_up_delay_days')}")
    print(DIVIDER)
    print()
