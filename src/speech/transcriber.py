"""Speech-to-text transcription using Whisper.cpp."""

import json
import subprocess
from pathlib import Path
from typing import Optional

from src.config import config
from src.utils.exceptions import ModelNotFoundError, STTError
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class WhisperTranscriber:
    """Transcribe audio files to text using Whisper.cpp."""

    def __init__(self) -> None:
        self.model_path = Path(config.stt.model_path)
        self._check_model()

    def _check_model(self) -> None:
        """Verify the Whisper model file exists."""
        if not self.model_path.exists():
            raise ModelNotFoundError(
                model_path=str(self.model_path),
                model_name=config.stt.model_name,
            )

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        word_timestamps: bool = False,
    ) -> dict:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio file.
            language: Language code (e.g., 'en', 'auto' for auto-detect).
            word_timestamps: Include word-level timestamps.

        Returns:
            Dict with 'text', 'segments', 'language', and 'duration'.

        Raises:
            STTError: If transcription fails.
        """
        if not audio_path.exists():
            raise STTError(
                f"Audio file not found: {audio_path}",
                audio_path=str(audio_path),
            )

        # Build whisper.cpp command
        cmd = [
            str(self._find_whisper_binary()),
            "--model",
            str(self.model_path),
            "--file",
            str(audio_path),
            "--threads",
            str(config.stt.num_threads),
            "--max-len",
            str(config.stt.chunk_seconds),
            "--language",
            language or config.stt.language,
            "--output-json",
        ]

        if word_timestamps:
            cmd.append("--word-timestamps")

        try:
            logger.info(
                "Starting transcription: %s (model=%s)",
                audio_path.name,
                self.model_path.name,
            )
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour max
            )

            if result.returncode != 0:
                raise STTError(
                    f"Whisper.cpp failed: {result.stderr.strip()}",
                    audio_path=str(audio_path),
                )

            # Parse JSON output
            output_path = audio_path.with_suffix(".json")
            if output_path.exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                output_path.unlink()  # Clean up temp file
            else:
                # Try to parse from stdout
                data = json.loads(result.stdout)

            text = data.get("text", "").strip()
            segments = data.get("segments", [])
            detected_language = data.get("language", language or "en")
            duration = data.get("duration", 0.0)

            logger.info(
                "Transcription complete: %s (%d chars, %s, %.1fs)",
                audio_path.name,
                len(text),
                detected_language,
                duration,
            )

            return {
                "text": text,
                "segments": segments,
                "language": detected_language,
                "duration": duration,
            }

        except subprocess.TimeoutExpired:
            raise STTError(
                "Transcription timed out (exceeded 1 hour)",
                audio_path=str(audio_path),
            )
        except json.JSONDecodeError as e:
            raise STTError(
                f"Failed to parse Whisper output: {e}",
                audio_path=str(audio_path),
            )
        except FileNotFoundError:
            raise STTError(
                "Whisper.cpp binary not found. "
                "Please build or download whisper.cpp and ensure it is in PATH.",
                audio_path=str(audio_path),
            )
        except Exception as e:
            raise STTError(
                f"Transcription failed: {e}",
                audio_path=str(audio_path),
            )

    def _find_whisper_binary(self) -> str:
        """Find the whisper.cpp executable.

        Returns:
            Path to the whisper binary.
        """
        import shutil

        binary = shutil.which("whisper")
        if binary:
            return binary
        # Common locations
        candidates = [
            "./whisper.cpp/main",
            "./whisper.cpp/build/bin/main",
            "whisper",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate
        return "whisper"  # Let subprocess fail with clear error

    def get_available_models(self) -> list:
        """List available Whisper model options.

        Returns:
            List of model dicts with name, size, and RAM requirements.
        """
        return [
            {"name": "ggml-tiny", "size_mb": 75, "ram_mb": 390, "speed": "fastest"},
            {"name": "ggml-base", "size_mb": 142, "ram_mb": 500, "speed": "fast"},
            {"name": "ggml-small", "size_mb": 466, "ram_mb": 1000, "speed": "balanced"},
            {"name": "ggml-medium", "size_mb": 1534, "ram_mb": 2500, "speed": "slow"},
        ]
