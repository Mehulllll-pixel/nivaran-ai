"""
pipeline_test.py
================
Standalone End-to-End Voice Pipeline Test:
  Audio/Transcript Input -> Whisper STT (if audio) -> Groq NLU -> Guardrails -> Dynamic Sarvam TTS Output

Response Dynamic Injection:
  - If action == "schedule_follow_up" and target_date is not None:
      - Uses natural date wording: "kal" (1 day), "parso" (2 days), or "DD Month" (e.g., "29 August")
      - If promised_amount is present: "Theek hai sir, hum aapke {amount} rupaye {date} ke liye note kar lete hain. Dhanyawaad!"
      - If promised_amount is null: "Theek hai sir, hum aapka payment {date} ke liye note kar lete hain. Dhanyawaad!"
  - If action == "generic_event_follow_up":
      - "Theek hai sir, hum aapke bataye anusar aapse follow-up karenge. Dhanyawaad!"
  - If action == "reconcile_payment":
      - "Theek hai, hum aapke payment records ko verify kar lete hain. Dhanyawaad!"
  - If action == "escalate_dispute":
      - "Aapka dispute note kar liya gaya hai, hamare executive aapse jald hi sampark karenge."
  - If action == "stop_channel_contact":
      - Contact blocked, no TTS generated.

Do NOT modify extraction.py, guardrails.py, or temporal_resolver.py.
"""

import os
import sys
import time
import base64
import json
import datetime
import subprocess
import numpy as np
import soundfile as sf
import torch
from transformers import pipeline as hf_pipeline
from sarvamai import SarvamAI

from extraction import extract_intent_and_promise
from guardrails import determine_recovery_action

CALL_DATE = datetime.datetime(2026, 8, 22, 12, 0, 0)
WHISPER_MODEL_ID = "Oriserve/Whisper-Hindi2Hinglish-Swift"


def format_spoken_date(target_date: datetime.datetime, call_date: datetime.datetime) -> str:
    """Formats a target date into natural Hinglish spoken phrasing relative to call_date."""
    delta_days = (target_date.date() - call_date.date()).days
    if delta_days == 1:
        return "kal"
    elif delta_days == 2:
        return "parso"
    else:
        # e.g. "29 August"
        return target_date.strftime("%d %B").lstrip("0")


def format_spoken_amount(amount: float) -> str:
    """Formats amount into clean integer or decimal string."""
    if amount is None:
        return ""
    if isinstance(amount, float) and amount.is_integer():
        return str(int(amount))
    return str(amount)


def build_spoken_response_text(
    recovery_action: dict,
    extraction_dict: dict,
    call_date: datetime.datetime
) -> str:
    """
    Constructs the natural spoken Hinglish response text by dynamically injecting
    promised_amount and resolved_date where appropriate.
    """
    action_type = recovery_action.get("action")
    target_date = recovery_action.get("target_date")
    amount = extraction_dict.get("promised_amount")

    if action_type == "schedule_follow_up":
        if target_date is not None:
            spoken_date = format_spoken_date(target_date, call_date)
            if amount is not None:
                amt_str = format_spoken_amount(amount)
                return f"Theek hai sir, hum aapke {amt_str} rupaye {spoken_date} ke liye note kar lete hain. Dhanyawaad!"
            else:
                return f"Theek hai sir, hum aapka payment {spoken_date} ke liye note kar lete hain. Dhanyawaad!"
        else:
            if amount is not None:
                amt_str = format_spoken_amount(amount)
                return f"Theek hai sir, hum aapke {amt_str} rupaye ka payment note kar lete hain. Dhanyawaad!"
            else:
                return "Theek hai, hum aapka payment follow-up schedule kar dete hain. Dhanyawaad!"

    elif action_type == "generic_event_follow_up":
        return "Theek hai sir, hum aapke bataye anusar aapse follow-up karenge. Dhanyawaad!"

    elif action_type == "reconcile_payment":
        return "Theek hai, hum aapke payment records ko verify kar lete hain. Dhanyawaad!"

    elif action_type == "escalate_dispute":
        return "Aapka dispute note kar liya gaya hai, hamare executive aapse jald hi sampark karenge."

    elif action_type == "stop_channel_contact":
        return ""

    return "Theek hai, hum aapka response note kar lete hain. Dhanyawaad!"


def read_audio_with_ffmpeg(file_path: str) -> np.ndarray:
    """Decodes audio from video/audio file into 16kHz mono float32 array using FFmpeg."""
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


def init_asr_pipeline():
    """Initializes the Whisper ASR pipeline."""
    if torch.cuda.is_available():
        device = "cuda:0"
        torch_dtype = torch.float16
        print("[INIT] Hardware acceleration: CUDA GPU (float16)")
    else:
        device = "cpu"
        torch_dtype = torch.float32
        print("[INIT] Hardware acceleration: CPU (float32)")

    print(f"[INIT] Loading Whisper model '{WHISPER_MODEL_ID}'...")
    t0 = time.time()
    pipe = hf_pipeline(
        "automatic-speech-recognition",
        model=WHISPER_MODEL_ID,
        torch_dtype=torch_dtype,
        device=device
    )
    print(f"[INIT] Whisper loaded in {time.time() - t0:.1f}s\n")
    return pipe


def generate_tts_response(text: str, output_path: str, sarvam_client: SarvamAI) -> dict:
    """Generates speech for the response text using Sarvam AI Bulbul TTS."""
    t0 = time.time()
    response = sarvam_client.text_to_speech.convert(
        text=text,
        language_code="hi-IN",
        model="bulbul:v3",
        output_audio_codec="wav"
    )
    gen_time = time.time() - t0

    if hasattr(response, "audios") and response.audios:
        audio_bytes = base64.b64decode(response.audios[0])
    elif hasattr(response, "audio"):
        audio_bytes = base64.b64decode(response.audio)
    else:
        raise RuntimeError(f"Unexpected TTS response structure: {response}")

    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    duration = None
    try:
        info = sf.info(output_path)
        duration = info.duration
    except Exception:
        pass

    return {
        "output_path": os.path.abspath(output_path),
        "file_size": len(audio_bytes),
        "duration": duration,
        "gen_time": gen_time
    }


def run_pipeline(
    input_source: str,
    asr_pipe,
    sarvam_client: SarvamAI,
    call_date: datetime.datetime,
    is_transcript: bool = False,
    output_prefix: str = "response"
):
    """Executes the pipeline on either an audio file path or a direct transcript."""
    print("=" * 70)
    print(f"PIPELINE RUN: {output_prefix}")
    print("=" * 70)
    print(f"Call Reference Date: {call_date.date()}")

    # Step 1: Input / STT Transcription
    if is_transcript:
        print("--- [STEP 1: DIRECT TRANSCRIPT INPUT] ---")
        transcript = input_source.strip()
        print(f"Input Transcript   : \"{transcript}\"\n")
    else:
        print("--- [STEP 1: WHISPER STT] ---")
        print(f"Input Audio Path   : {input_source}")
        t_stt_start = time.time()
        audio_data = read_audio_with_ffmpeg(input_source)
        asr_result = asr_pipe({"raw": audio_data, "sampling_rate": 16000})
        transcript = asr_result.get("text", "").strip()
        stt_duration = time.time() - t_stt_start
        print(f"STT Processing Time : {stt_duration:.2f}s")
        print(f"Raw Transcript      : \"{transcript}\"\n")

    # Step 2: NLU Extraction & Date Resolution
    print("--- [STEP 2: GROQ NLU EXTRACTION & TEMPORAL RESOLUTION] ---")
    t_nlu_start = time.time()
    extraction_result = extract_intent_and_promise(transcript, call_date)
    nlu_duration = time.time() - t_nlu_start

    print("RAW GROQ RESPONSE:")
    print(extraction_result["raw_response"])
    print()

    print("PARSED EXTRACTION:")
    print(json.dumps(extraction_result["extraction"], indent=2, default=str))
    print()

    print(f"PYTHON RESOLVED PROMISED DATE : {extraction_result['resolved_promised_date']}")
    print(f"NLU Processing Time           : {nlu_duration:.2f}s\n")

    # Step 3: Guardrail & Action Determination
    print("--- [STEP 3: GUARDRAILS / RECOVERY ACTION] ---")
    recovery_action = determine_recovery_action(extraction_result)
    print(json.dumps(recovery_action, indent=2, default=str))
    print()

    # Step 4: Spoken Response Generation (TTS)
    print("--- [STEP 4: DYNAMIC RESPONSE SYNTHESIS (SARVAM TTS)] ---")
    action_type = recovery_action.get("action")
    is_blocked = recovery_action.get("compliance_block", False)

    if is_blocked or action_type == "stop_channel_contact":
        print("[ACTION: STOP CONTACT] Compliance block active. No TTS audio response will be generated.")
        tts_result = None
    else:
        response_text = build_spoken_response_text(
            recovery_action,
            extraction_result["extraction"],
            call_date
        )
        out_audio_path = f"{output_prefix}.wav"

        print(f"Selected Spoken Response: \"{response_text}\"")
        tts_result = generate_tts_response(response_text, out_audio_path, sarvam_client)
        print(f"TTS Output File Path    : {tts_result['output_path']}")
        print(f"TTS Generation Time     : {tts_result['gen_time']:.2f}s")
        print(f"TTS Audio Duration      : {tts_result['duration']:.2f}s" if tts_result['duration'] else "TTS Audio Duration      : N/A")
        print(f"TTS File Size           : {tts_result['file_size']} bytes")

    print("\n" + "-" * 70)
    print("PIPELINE SUMMARY:")
    print(f"  Input Source     : {input_source}")
    print(f"  Transcript       : \"{transcript}\"")
    print(f"  Intent           : {extraction_result['extraction'].get('intent')}")
    print(f"  Promised Amount  : {extraction_result['extraction'].get('promised_amount')}")
    print(f"  Temporal Type    : {extraction_result['extraction'].get('temporal', {}).get('type')}")
    print(f"  Resolved Date    : {extraction_result['resolved_promised_date']}")
    print(f"  Action           : {recovery_action.get('action')}")
    print(f"  Spoken Text      : \"{response_text if (not is_blocked and action_type != 'stop_channel_contact') else '[NONE]'}\"")
    print(f"  Response Audio   : {tts_result['output_path'] if tts_result else 'None (Contact Stopped)'}")
    print("-" * 70 + "\n")


def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("[ERROR] GROQ_API_KEY environment variable is not set.")
        sys.exit(1)

    if not os.environ.get("SARVAM_API_KEY"):
        print("[ERROR] SARVAM_API_KEY environment variable is not set.")
        sys.exit(1)

    # Initialize components
    asr_pipe = init_asr_pipeline()
    sarvam_client = SarvamAI()

    # Run 1: Real audio recording1.mp4 (promised_amount is null, date is tomorrow -> kal)
    recording1_path = "audio/recording1.mp4"
    if os.path.exists(recording1_path):
        run_pipeline(
            input_source=recording1_path,
            asr_pipe=asr_pipe,
            sarvam_client=sarvam_client,
            call_date=CALL_DATE,
            is_transcript=False,
            output_prefix="response_recording1"
        )
    else:
        print(f"[ERROR] Audio file not found: {recording1_path}")

    # Run 2: Handcrafted hero test case (amount + near-term date)
    hero_transcript = "5000 rupaye kal de dunga."
    run_pipeline(
        input_source=hero_transcript,
        asr_pipe=asr_pipe,
        sarvam_client=sarvam_client,
        call_date=CALL_DATE,
        is_transcript=True,
        output_prefix="response_hero_5000_kal"
    )


if __name__ == "__main__":
    main()
