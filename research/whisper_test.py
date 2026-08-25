import torch
from transformers import pipeline
import time
import subprocess
import numpy as np
import os

def read_audio_with_ffmpeg(file_path):
    """
    Decodes the audio track of a video or audio file using FFmpeg
    and returns a float32 1D numpy array sampled at 16000Hz (mono).
    """
    command = [
        "ffmpeg",
        "-i", file_path,
        "-f", "f32le",        # Raw PCM 32-bit float, little-endian
        "-acodec", "pcm_f32le",
        "-ar", "16000",       # Resample to 16kHz
        "-ac", "1",           # Downmix to mono
        "-y",                 # Automatically overwrite output files
        "-"                   # Redirect output to stdout / pipe
    ]
    
    # Run the FFmpeg command
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed with exit code {process.returncode}:\n"
            f"{stderr.decode('utf-8', errors='ignore')}"
        )
        
    # Convert binary buffer to numpy float32 array
    audio_array = np.frombuffer(stdout, dtype=np.float32)
    return audio_array

def main():
    # 1. Detect hardware acceleration
    if torch.cuda.is_available():
        device = "cuda:0"
        torch_dtype = torch.float16
        print("CUDA GPU is available. Running with float16 on GPU.")
    else:
        device = "cpu"
        torch_dtype = torch.float32
        print("CUDA GPU is NOT available. Running with float32 on CPU. Note: This may be slower.")

    # 2. Initialize the ASR pipeline
    model_id = "Oriserve/Whisper-Hindi2Hinglish-Swift"
    print(f"Loading model '{model_id}'...")
    try:
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model_id,
            torch_dtype=torch_dtype,
            device=device
        )
        print("Model loaded successfully.\n")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 3. Test remaining two files sequentially
    files_to_test = ["audio/recording2.mp4", "audio/recording3.mp4"]
    for filepath in files_to_test:
        filename = os.path.basename(filepath)
        file_start_time = time.time()
        
        try:
            # Decode MP4 audio using FFmpeg
            ffmpeg_start = time.time()
            audio_data = read_audio_with_ffmpeg(filepath)
            ffmpeg_end = time.time()
            ffmpeg_dur = ffmpeg_end - ffmpeg_start
            
            # Transcribe audio data
            transcribe_start = time.time()
            result = pipe({"raw": audio_data, "sampling_rate": 16000})
            transcribe_end = time.time()
            whisper_dur = transcribe_end - transcribe_start
            
            total_dur = time.time() - file_start_time
            
            # Print formatted output
            print("=" * 50)
            print(f"FILE: {filename}")
            print("=" * 50)
            print("TRANSCRIPTION:")
            print(result.get("text", "").strip())
            print()
            print(f"FFmpeg decoding time: {ffmpeg_dur:.2f} seconds")
            print(f"Whisper transcription time: {whisper_dur:.2f} seconds")
            print(f"Total time: {total_dur:.2f} seconds")
            print("=" * 50)
            print()
            
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found.\n")
        except Exception as e:
            print(f"An error occurred while processing '{filename}': {e}\n")

if __name__ == "__main__":
    main()
