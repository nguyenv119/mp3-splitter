#!/usr/bin/env python3
"""
Usage:
    python main.py input.mp3 -d 300 -o output
"""

import argparse
import math
import subprocess
import sys
from pathlib import Path
from pydub.utils import which
from faster_whisper import WhisperModel


def validate_ffmpeg():
    """Ensure ffmpeg is available on the system."""
    if not which("ffmpeg"):
        print("Error: ffmpeg is required but not found. Please install ffmpeg.")
        sys.exit(1)


def get_audio_duration(input_file: Path) -> float:
    """Return duration of audio file in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_file)
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return float(out.strip())
    except Exception as e:
        raise RuntimeError(f"Failed to get duration: {e}")


def transcribe_chunk(file_path: Path, model) -> str:
    """Transcribe a chunk using Faster-Whisper."""
    segments, _ = model.transcribe(str(file_path))
    return " ".join(seg.text for seg in segments)


def split_audio_only(input_file, output_dir, chunk_duration, overlap, fmt="wav"):
    """
    Just split audio into chunks, no transcription.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = get_audio_duration(input_file)

    step = chunk_duration - overlap
    if step <= 0:
        raise ValueError("Overlap must be less than chunk duration")

    num_chunks = math.ceil((duration - overlap) / step)
    print(f"Audio duration: {duration:.2f} sec | "
          f"Chunk: {chunk_duration}s | Overlap: {overlap}s | "
          f"Chunks: {num_chunks}")

    base_name = input_file.stem

    for i in range(num_chunks):
        start = i * step
        end = min(start + chunk_duration, duration)

        out_file = output_dir / f"{base_name}_chunk_{i+1:03d}.{fmt}"
        print(f"Creating chunk {i+1}/{num_chunks} → {out_file.name}")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_file),
            "-ss", str(start),
            "-t", str(end - start),
            str(out_file)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"\n✅ Finished: {num_chunks} chunks saved to {output_dir}")
    return num_chunks


def split_and_transcribe(input_file, output_dir, chunk_duration, overlap, fmt="wav", model_size="small"):
    """
    Split audio into chunks and transcribe each chunk incrementally.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = get_audio_duration(input_file)

    step = chunk_duration - overlap
    if step <= 0:
        raise ValueError("Overlap must be less than chunk duration")

    num_chunks = math.ceil((duration - overlap) / step)
    print(f"Audio duration: {duration:.2f} sec | "
          f"Chunk: {chunk_duration}s | Overlap: {overlap}s | "
          f"Chunks: {num_chunks}")

    print(f"\nLoading Faster-Whisper model: {model_size}")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    base_name = input_file.stem
    transcript_file = output_dir / f"{base_name}_transcript.txt"

    with open(transcript_file, "w", encoding="utf-8") as f:
        for i in range(num_chunks):
            start = i * step
            end = min(start + chunk_duration, duration)

            out_file = output_dir / f"{base_name}_chunk_{i+1:03d}.wav"
            print(f"\nCreating chunk {i+1}/{num_chunks} → {out_file.name}")

            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_file),
                "-ss", str(start),
                "-t", str(end - start),
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                str(out_file)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            print(f"Transcribing {out_file.name}...")
            text = transcribe_chunk(out_file, model)

            f.write(f"[Chunk {i+1}] {text.strip()}\n\n")
            f.flush()
            print(f"→ Added transcript for chunk {i+1}")

    print(f"\n✅ Finished: transcript saved to {transcript_file}")
    return transcript_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to input MP3 file")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("-d", "--duration", type=int, default=300, help="Chunk duration in seconds")
    parser.add_argument("-l", "--overlap", type=int, default=0, help="Overlap in seconds")
    parser.add_argument("-f", "--format", default="mp3", help="Output format (default: mp3)")
    parser.add_argument("-m", "--model", default="small", help="Whisper model size (tiny, base, small, medium, large)")

    args = parser.parse_args()

    validate_ffmpeg()
    input_file = Path(args.input_file)
    output_dir = Path(args.output)

    if not input_file.exists():
        sys.exit(f"File not found: {input_file}")

    # Ask user if they want transcription
    choice = input("Do you want to transcribe after splitting? (y/n): ").strip().lower()

    if choice == "y":
        split_and_transcribe(input_file, output_dir, args.duration, args.overlap, args.format, args.model)
    else:
        split_audio_only(input_file, output_dir, args.duration, args.overlap, args.format)


if __name__ == "__main__":
    main()
