"""
regression_test_step2.py
========================
Step 2: End-to-end test for recording3.mp4.

Pipeline:
  FFmpeg → Whisper (Oriserve/Whisper-Hindi2Hinglish-Swift)
         → extract_intent_and_promise()
         → determine_recovery_action()

Rules:
  - Do NOT pre-clean or correct the Whisper transcript before sending to Groq.
  - Use the SAME FFmpeg + Whisper setup as whisper_test.py (copied verbatim).
  - whisper_test.py is NOT imported or modified.

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

AUDIO_FILE = "audio/recording3.mp4"
CALL_DATE  = datetime.datetime(2026, 8, 22, 12, 0, 0)
MODEL_ID   = "Oriserve/Whisper-Hindi2Hinglish-Swift"

DIVIDER = "=" * 60


# ── Copied verbatim from whisper_test.py — do NOT import that file ──────────

def read_audio_with_ffmpeg(file_path: str) -> np.ndarray:
    """
    Decodes the audio track of a video or audio file using FFmpeg
    and returns a float32 1D numpy array sampled at 16000Hz (mono).
    """
    command = [
        "ffmpeg",
        "-i", file_path,
        "-f", "f32le",
        "-acodec", "pcm_f32le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        "-"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed with exit code {process.returncode}:\n"
            f"{stderr.decode('utf-8', errors='ignore')}"
        )
    return np.frombuffer(stdout, dtype=np.float32)


# ────────────────────────────────────────────────────────────────────────────

print(DIVIDER)
print("RECORDING 3 — REAL AUDIO TEST")
print(DIVIDER)
print(f"Audio file : {AUDIO_FILE}")
print(f"Call date  : {CALL_DATE.date()}")
print()

# ── Step 1: Load Whisper ─────────────────────────────────────────────────────
whisper_ok = False
whisper_transcript = ""

if torch.cuda.is_available():
    device = "cuda:0"
    torch_dtype = torch.float16
    print("Hardware: CUDA GPU (float16)")
else:
    device = "cpu"
    torch_dtype = torch.float32
    print("Hardware: CPU (float32)")

print(f"Loading Whisper model '{MODEL_ID}'...")
t0 = time.time()
try:
    asr_pipe = hf_pipeline(
        "automatic-speech-recognition",
        model=MODEL_ID,
        torch_dtype=torch_dtype,
        device=device
    )
    print(f"Model loaded in {time.time() - t0:.1f}s\n")
    whisper_loaded = True
except Exception as e:
    print(f"[FAIL] Whisper model load error: {e}\n")
    whisper_loaded = False

# ── Step 2: FFmpeg decode + Whisper transcribe ───────────────────────────────
if whisper_loaded:
    try:
        t1 = time.time()
        audio_data = read_audio_with_ffmpeg(AUDIO_FILE)
        ffmpeg_dur = time.time() - t1
        print(f"FFmpeg decode: {ffmpeg_dur:.2f}s")

        t2 = time.time()
        asr_result = asr_pipe({"raw": audio_data, "sampling_rate": 16000})
        whisper_dur = time.time() - t2
        whisper_transcript = asr_result.get("text", "").strip()
        whisper_ok = True
        print(f"Whisper transcription: {whisper_dur:.2f}s")
    except FileNotFoundError:
        print(f"[FAIL] Audio file not found: {AUDIO_FILE}")
    except Exception as e:
        print(f"[FAIL] Whisper transcription error: {e}")
else:
    print("[SKIP] Whisper step skipped due to model load failure.")

print()
print("Raw Whisper transcript:")
print(whisper_transcript if whisper_transcript else "[EMPTY — transcription failed]")
print()

# ── Step 3: Groq extraction ───────────────────────────────────────────────────
groq_ok = False
extraction_valid = False
result = None

if whisper_ok and whisper_transcript:
    try:
        result = extract_intent_and_promise(whisper_transcript, CALL_DATE)
        groq_ok = not result["fallback_mode"]
        ext = result["extraction"]

        required_keys = {"intent", "sentiment", "promised_amount", "temporal", "confidence", "reasoning"}
        extraction_valid = required_keys.issubset(ext.keys())

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
        print(f"[FAIL] Groq extraction error: {e}")
else:
    print("[SKIP] Groq extraction skipped — no valid transcript.")

# ── Step 4: Guardrail / recovery action ──────────────────────────────────────
action = None
guardrail_ok = False

if result is not None:
    try:
        action = determine_recovery_action(result)
        guardrail_ok = True
        print("GUARDRAIL / RECOVERY ACTION:")
        print(json.dumps(action, indent=2, default=str))
        print()
    except Exception as e:
        print(f"[FAIL] Guardrail error: {e}")
else:
    print("[SKIP] Guardrail skipped — no extraction result.")

# ── Diagnostic report ─────────────────────────────────────────────────────────
print(DIVIDER)
print("DIAGNOSTIC REPORT")
print(DIVIDER)
print(f"  Whisper succeeded         : {'YES' if whisper_ok else 'NO'}")
print(f"  Groq strict json_schema   : {'SUCCEEDED' if groq_ok else 'FALLBACK/FAILED'}")
print(f"  Extraction structure valid: {'YES' if extraction_valid else 'NO'}")

if result is not None:
    ext = result["extraction"]
    print(f"  Intent                    : {ext.get('intent', 'N/A')}")
    print(f"  Temporal type             : {ext.get('temporal', {}).get('type', 'N/A')}")
    print(f"  event_trigger             : {ext.get('temporal', {}).get('event_trigger', 'N/A')}")
    print(f"  Resolved date             : {result['resolved_promised_date']}")

if action is not None:
    print(f"  Action                    : {action.get('action', 'N/A')}")
    print(f"  compliance_block          : {action.get('compliance_block')}")
    print(f"  escalate_to_human         : {action.get('escalate_to_human')}")
    print(f"  reconciliation_required   : {action.get('reconciliation_required')}")
    print(f"  generic_follow_up         : {action.get('generic_follow_up')}")
    print(f"  follow_up_delay_days      : {action.get('follow_up_delay_days')}")

print(DIVIDER)
