"""
VELES Serbian Piper TTS
"""

import os
import subprocess
import tempfile
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PIPER_EXECUTABLE = _PROJECT_ROOT / "venv" / "bin" / "piper"
PIPER_MODEL_PATH = _PROJECT_ROOT / "models" / "veles-serbian.onnx"

# Serbian speech tuning
SPEAKER = "0"
LENGTH_SCALE = "1.12"
NOISE_SCALE = "0.667"
NOISE_W_SCALE = "0.8"
SENTENCE_SILENCE = "0.18"


def synthesize_to_file(text: str) -> str:
    """Generate Serbian WAV using the trained Piper voice."""

    text = (text or "").strip()

    if not text:
        raise RuntimeError("TTS text is empty.")

    if not PIPER_EXECUTABLE.exists():
        raise RuntimeError(
            f"Piper executable not found: {PIPER_EXECUTABLE}"
        )

    if not PIPER_MODEL_PATH.exists():
        raise RuntimeError(
            f"Piper voice model not found: {PIPER_MODEL_PATH}"
        )

    fd, output_path = tempfile.mkstemp(
        suffix=".wav",
        prefix="veles_tts_"
    )
    os.close(fd)

    command = [
        str(PIPER_EXECUTABLE),
        "--model",
        str(PIPER_MODEL_PATH),
        "--output_file",
        output_path,
        "--speaker",
        SPEAKER,
        "--length-scale",
        LENGTH_SCALE,
        "--noise-scale",
        NOISE_SCALE,
        "--noise-w-scale",
        NOISE_W_SCALE,
        "--sentence-silence",
        SENTENCE_SILENCE,
    ]

    try:
        process = subprocess.run(
            command,
            input=text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )

        if process.returncode != 0:
            raise RuntimeError(
                f"Piper TTS failed:\n{process.stderr.strip()}"
            )

        if not os.path.exists(output_path):
            raise RuntimeError(
                "Piper completed successfully but did not create the WAV file."
            )

        if os.path.getsize(output_path) == 0:
            raise RuntimeError("Piper created an empty WAV file.")

        return output_path

    except subprocess.TimeoutExpired:
        raise RuntimeError("Piper TTS timed out after 60 seconds.")

    except Exception:
        try:
            if os.path.exists(output_path):
                os.unlink(output_path)
        except OSError:
            pass
        raise
