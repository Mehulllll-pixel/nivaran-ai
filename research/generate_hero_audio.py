"""
generate_hero_audio.py
======================
Generates the static audio file for the hero demo event's agent response
using Sarvam AI TTS (Bulbul v3 model) and saves it to frontend/public/hero-demo-response.mp3.
"""

import os
import sys
import time
import base64
from pathlib import Path

# Load from research/.env, backend/.env, or system environment
env_paths = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / "backend" / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]

for env_path in env_paths:
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k and v and k not in os.environ:
                        os.environ[k] = v

SARVAM_KEY = os.environ.get("SARVAM_API_KEY")

if not SARVAM_KEY:
    print("[ERROR] SARVAM_API_KEY not found in environment or .env files.")
    print("Please set SARVAM_API_KEY in research/.env")
    sys.exit(1)

from sarvamai import SarvamAI

TEXT = "Theek hai sir, hum aapke 12000 rupaye kal ke liye note kar lete hain. Dhanyawaad!"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "frontend" / "public" / "hero-demo-response.mp3"

def main():
    print("=" * 60)
    print("GENERATING HERO DEMO AUDIO VIA SARVAM AI TTS")
    print(f"Text: \"{TEXT}\"")
    print(f"Target: {OUTPUT_FILE}")
    print("=" * 60)

    client = SarvamAI(api_subscription_key=SARVAM_KEY)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    try:
        # Request MP3 codec from Sarvam
        response = client.text_to_speech.convert(
            text=TEXT,
            language_code="hi-IN",
            model="bulbul:v3",
            output_audio_codec="mp3"
        )
    except Exception as e:
        # Fallback to wav if mp3 codec not supported directly, then save
        print(f"[INFO] Direct MP3 request failed ({e}), attempting standard convert...")
        response = client.text_to_speech.convert(
            text=TEXT,
            language_code="hi-IN",
            model="bulbul:v3"
        )

    elapsed = time.time() - t0

    audio_bytes = None
    if hasattr(response, "audios") and response.audios:
        audio_bytes = base64.b64decode(response.audios[0])
    elif hasattr(response, "audio") and response.audio:
        audio_bytes = base64.b64decode(response.audio)
    elif isinstance(response, dict):
        if "audios" in response and response["audios"]:
            audio_bytes = base64.b64decode(response["audios"][0])
        elif "audio" in response and response["audio"]:
            audio_bytes = base64.b64decode(response["audio"])

    if not audio_bytes:
        print(f"[ERROR] Could not extract audio bytes from response: {response}")
        sys.exit(1)

    with open(OUTPUT_FILE, "wb") as f:
        f.write(audio_bytes)

    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"[SUCCESS] Audio successfully generated in {elapsed:.2f}s")
    print(f"[SUCCESS] Output file: {OUTPUT_FILE} ({file_size} bytes)")
    print("=" * 60)

if __name__ == "__main__":
    main()
