"""
Voice pipeline for Nivaran's Hinglish recovery calls.

Three pieces, each using the best available tool rather than anything
built/trained from scratch:

  1. STT  -> Oriserve/Whisper-Hindi2Hinglish-Swift (HuggingFace)
             Purpose-built Hinglish transcription, runs locally, no training.
  2. NLU  -> Groq API (Llama 3.3 70B)
             Extracts intent + promise-to-pay details as structured JSON.
             Fast (sub-second) and free-tier, which matters for a voice loop.
  3. TTS  -> harrrshall/hinglish-tts (open-source, GitHub)
             Generates the agent's spoken response in natural Hinglish.

Setup required before this module works:
  pip install transformers torch groq
  git clone https://github.com/harrrshall/hinglish-tts && pip install -e hinglish-tts
  export GROQ_API_KEY="..."   (free at console.groq.com)

Models are loaded once at module import (lazy singletons below) so repeated
calls in a batch demo don't reload weights every time.
"""
import json
import os
from functools import lru_cache

# NOTE: groq, transformers, and torch are imported lazily inside the
# functions that need them (not at module load time). This means the
# fallback path in executors.py — used when no demo audio clip is
# attached to an event — still works even before you've installed
# these heavier dependencies. Install them only once you're ready to
# wire in the real STT/NLU/TTS calls.

# --- STT: Oriserve Hinglish Whisper -----------------------------------------

@lru_cache(maxsize=1)
def _get_stt_model():
    """Lazy-loads the STT model once. Cached so repeated calls are fast."""
    import torch
    from transformers import WhisperProcessor, WhisperForConditionalGeneration

    repo = "Oriserve/Whisper-Hindi2Hinglish-Swift"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = WhisperProcessor.from_pretrained(repo)
    model = WhisperForConditionalGeneration.from_pretrained(repo).to(device)
    model.eval()
    return processor, model, device


def transcribe_hinglish(audio_path: str) -> str:
    """
    Transcribes a WAV file (16kHz mono) to Hinglish text.
    In the demo flow, this is fed a pre-recorded customer response clip.
    """
    import torch
    import soundfile as sf

    processor, model, device = _get_stt_model()
    audio, sr = sf.read(audio_path)

    input_features = processor(
        audio, sampling_rate=sr, return_tensors="pt"
    ).input_features.to(device)

    with torch.no_grad():
        predicted_ids = model.generate(input_features)

    transcript = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return transcript.strip()


# --- NLU: Groq for intent + promise-to-pay extraction -----------------------

_groq_client = None


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq  # lazy import — see note at top of file
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Get a free key at console.groq.com")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


EXTRACTION_SYSTEM_PROMPT = """You are analyzing a transcript from a payment recovery call in India. \
The customer was contacted about an overdue/failed payment. Extract structured information \
from what they said. The text may be in Hindi, English, or Hinglish (mixed).

Respond ONLY with valid JSON, no other text, in this exact shape:
{
  "intent": "agree_to_pay" | "promise_future_payment" | "asks_why" | "cannot_pay" | "opt_out" | "unclear",
  "sentiment": "neutral" | "cooperative" | "frustrated" | "angry",
  "promised_amount": <number or null>,
  "promised_date": "<ISO date string or a relative description like 'tomorrow', or null>",
  "confidence": "high" | "medium" | "low",
  "reasoning": "<one sentence explaining the extraction>"
}

If the customer didn't mention a specific amount, assume it matches the amount they were \
called about (provided in context) unless they explicitly disputed the amount.
"""


def extract_intent_and_promise(transcript: str, amount_at_risk: float) -> dict:
    """
    Sends the transcript to Groq (Llama 3.3 70B) for structured extraction.
    This is the "understand customer intent + extract promise-to-pay" step
    in the core flow.
    """
    client = _get_groq_client()

    user_message = (
        f"Amount the customer was called about: ₹{amount_at_risk}\n"
        f"Transcript: \"{transcript}\""
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,  # low temperature — this is extraction, not creative generation
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if the model ever returns malformed JSON — don't crash the demo
        return {
            "intent": "unclear",
            "sentiment": "neutral",
            "promised_amount": None,
            "promised_date": None,
            "confidence": "low",
            "reasoning": "Extraction failed to parse — raw model output was not valid JSON.",
        }


# --- TTS: open-source Hinglish TTS -------------------------------------------

@lru_cache(maxsize=1)
def _get_tts_model():
    """
    Lazy-loads the Hinglish TTS model.
    Requires: git clone https://github.com/harrrshall/hinglish-tts && pip install -e hinglish-tts
    Check that repo's README for its exact import path — this wraps the
    expected interface based on their documented usage.
    """
    from hinglish_tts import HinglishTTS  # adjust import if the package structure differs
    return HinglishTTS()


def synthesize_hinglish_speech(text: str, output_path: str) -> str:
    """
    Generates spoken audio for the agent's side of the conversation.
    Returns the path to the generated audio file.
    """
    tts = _get_tts_model()
    tts.synthesize(text, output_path=output_path)
    return output_path


# --- Recovery script templates, by root cause --------------------------------

RECOVERY_SCRIPTS = {
    "bank_timeout": "Namaste! Aapka payment complete nahi ho paya technical issue ki wajah se. Kya aap abhi retry karna chahenge?",
    "insufficient_funds": "Namaste! Aapka payment fail ho gaya tha. Kya aap bata sakte hain ki aap kab tak payment kar payenge?",
    "user_abandoned": "Namaste! Maine dekha aapne checkout complete nahi kiya tha. Kya kisi cheez mein help chahiye, ya aap baad mein complete karenge?",
    "invoice_unpaid": "Namaste! Aapka invoice abhi tak pending hai. Kya aap bata sakte hain ki payment kab tak ho payega?",
}


def get_opening_script(root_cause: str) -> str:
    return RECOVERY_SCRIPTS.get(
        root_cause,
        "Namaste! Hum aapke payment ke baare mein baat karna chahte hain. Kya aap abhi baat kar sakte hain?",
    )
