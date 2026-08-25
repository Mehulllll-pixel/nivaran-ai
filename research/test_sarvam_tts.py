"""
test_sarvam_tts.py
==================
Standalone synthesis test for Sarvam AI TTS (Bulbul model).
Synthesizes 3 test lines and saves output audio files in the workspace.
Measures generation time, file size, duration, and inspects response metadata.
"""

import os
import sys
import time
import base64
import soundfile as sf
from sarvamai import SarvamAI

LINES = [
    {
        "id": "A",
        "text": "Namaste! Aapka payment complete nahi ho paya. Kya aap abhi retry karna chahenge?",
        "output_file": "sarvam_tts_line_A.wav"
    },
    {
        "id": "B",
        "text": "Namaste! Aapka payment abhi tak pending hai. Kya aap bata sakte hain ki payment kab tak ho payega?",
        "output_file": "sarvam_tts_line_B.wav"
    },
    {
        "id": "C",
        "text": "Theek hai sir, hum aapke 2000 rupaye abhi note kar lete hain, aur baaki agle hafte ke liye follow-up schedule kar dete hain.",
        "output_file": "sarvam_tts_line_C.wav"
    }
]

def main():
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        print("[ERROR] SARVAM_API_KEY environment variable is not set.")
        sys.exit(1)

    print("=" * 65)
    print("SARVAM AI TTS STANDALONE SYNTHESIS TEST")
    print("=" * 65)

    client = SarvamAI()

    results = []

    for item in LINES:
        line_id = item["id"]
        text = item["text"]
        out_filename = item["output_file"]
        out_path = os.path.abspath(out_filename)

        print(f"\n--- Line {line_id} ---")
        print(f"Text: \"{text}\"")

        start_time = time.time()
        success = False
        error_msg = None
        warning_msg = None
        duration = None
        file_size = None
        fmt = "WAV"
        credits_info = "N/A"

        try:
            # Using bulbul:v3 with Hindi language code (hi-IN)
            response = client.text_to_speech.convert(
                text=text,
                language_code="hi-IN",
                model="bulbul:v3",
                output_audio_codec="wav"
            )
            gen_time = time.time() - start_time

            # The response typically has an 'audios' list of base64 encoded audio strings
            if hasattr(response, "audios") and response.audios:
                audio_base64 = response.audios[0]
                audio_bytes = base64.b64decode(audio_base64)
                with open(out_path, "wb") as f:
                    f.write(audio_bytes)
                success = True
            elif hasattr(response, "audio"):
                audio_bytes = base64.b64decode(response.audio)
                with open(out_path, "wb") as f:
                    f.write(audio_bytes)
                success = True
            else:
                # Raw response inspection if structured differently
                print(f"[DEBUG] Response structure: {type(response)} -> {response}")
                error_msg = f"Unexpected response format: {type(response)}"

            if success and os.path.exists(out_path):
                file_size = os.path.getsize(out_path)
                try:
                    info = sf.info(out_path)
                    duration = info.duration
                    fmt = info.format
                except Exception as ex:
                    warning_msg = f"Could not read duration with soundfile: {ex}"

        except Exception as e:
            gen_time = time.time() - start_time
            error_msg = str(e)
            success = False

        results.append({
            "id": line_id,
            "text": text,
            "file_path": out_path,
            "gen_time": gen_time,
            "format": fmt,
            "duration": duration,
            "file_size": file_size,
            "success": success,
            "error": error_msg,
            "warning": warning_msg,
            "credits": credits_info
        })

    print("\n" + "=" * 65)
    print("TECHNICAL VERIFICATION REPORT")
    print("=" * 65)

    all_passed = True
    for r in results:
        print(f"\n[Line {r['id']}]")
        print(f"  Exact output file path       : {r['file_path']}")
        print(f"  Generation time              : {r['gen_time']:.2f}s")
        print(f"  Generated file format        : {r['format']}")
        print(f"  Duration                     : {r['duration']:.2f}s" if r['duration'] is not None else "  Duration                     : N/A")
        print(f"  File size                    : {r['file_size']} bytes" if r['file_size'] is not None else "  File size                    : N/A")
        print(f"  Synthesis completed          : {'SUCCESS' if r['success'] else 'FAILED'}")
        print(f"  Warnings                     : {r['warning'] or 'None'}")
        print(f"  Errors                       : {r['error'] or 'None'}")
        print(f"  Credits/cost info in response: {r['credits']}")

        # Verification checks
        file_exists = os.path.exists(r['file_path']) and os.path.getsize(r['file_path']) > 0
        dur_valid = r['duration'] is not None and r['duration'] > 0
        if not (r['success'] and file_exists and dur_valid):
            all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print("ALL 3 TTS FILES SUCCESSFULLY GENERATED AND TECHNICALLY VERIFIED.")
    else:
        print("SOME TTS GENERATIONS FAILED TECHNICAL VERIFICATION.")
    print("=" * 65)

if __name__ == "__main__":
    main()
