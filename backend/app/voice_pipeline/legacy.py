"""
Legacy voice pipeline helper functions.
"""
import json
import os
from functools import lru_cache

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


# --- TTS: open-source Hinglish TTS -------------------------------------------

@lru_cache(maxsize=1)
def _get_tts_model():
    """
    Lazy-loads the Hinglish TTS model.
    """
    from hinglish_tts import HinglishTTS
    return HinglishTTS()


def synthesize_hinglish_speech(text: str, output_path: str) -> str:
    """
    Generates spoken audio for the agent's side of the conversation.
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
