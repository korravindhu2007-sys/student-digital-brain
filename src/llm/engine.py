"""Local LLM inference engine using llama.cpp with Phi-3 Mini GGUF."""

import json
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from src.config import config
from src.utils.exceptions import LLMError, ModelNotFoundError
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class LLMEngine:
    """Local LLM inference engine wrapping llama.cpp with Phi-3 Mini.

    Manages model lifecycle: lazy loading, inference, and memory cleanup.
    """

    def __init__(self) -> None:
        self.model_path = Path(config.llm.model_path)
        self._model = None
        self._loaded = False

    def _check_model(self) -> None:
        """Verify the model file exists."""
        if not self.model_path.exists():
            raise ModelNotFoundError(
                model_path=str(self.model_path),
                model_name="Phi-3-mini-4k-instruct-q4_k_m.gguf",
            )

    def _initialize_llamacpp(self) -> None:
        """Load the llama.cpp library and model."""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise LLMError(
                "llama-cpp-python is not installed. Install with: pip install llama-cpp-python"
            )

        self._check_model()
        logger.info("Loading model: %s", self.model_path)

        self._model = Llama(
            model_path=str(self.model_path),
            n_ctx=config.llm.n_ctx,
            n_threads=config.llm.n_threads,
            n_batch=config.llm.n_batch,
            verbose=False,
        )
        self._loaded = True
        logger.info("Model loaded successfully")

    @property
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory."""
        return self._loaded and self._model is not None

    def load(self) -> None:
        """Explicitly load the model into memory."""
        if not self.is_loaded:
            self._initialize_llamacpp()

    def unload(self) -> None:
        """Unload the model from memory to free RAM."""
        if self._model is not None:
            self._model = None
            self._loaded = False
            logger.info("Model unloaded from memory")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[List[str]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Generate text using the LLM.

        Args:
            prompt: User input text.
            system_prompt: System instruction for model behavior.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0-1.0).
            stop: Stop sequences.
            stream: Whether to stream the output.

        Returns:
            Dict with 'text', 'tokens_used', 'tokens_per_second'.

        Raises:
            LLMError: If inference fails.
        """
        if not self.is_loaded:
            self.load()

        # Build full prompt with optional system message
        if system_prompt:
            full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n"
        else:
            full_prompt = f"<|user|>\n{prompt}\n<|assistant|>\n"

        params = {
            "prompt": full_prompt,
            "max_tokens": max_tokens or config.llm.max_tokens,
            "temperature": temperature if temperature is not None else config.llm.temperature,
            "top_p": config.llm.top_p,
            "top_k": config.llm.top_k,
            "repeat_penalty": config.llm.repeat_penalty,
            "stop": stop or [],
            "echo": False,
        }

        try:
            start_time = time.time()

            if stream:
                return self._generate_stream(params, start_time)
            else:
                return self._generate_complete(params, start_time)

        except Exception as e:
            raise LLMError(f"LLM inference failed: {e}")

    def _generate_complete(self, params: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Run complete (non-streaming) inference."""
        output = self._model.create_completion(**params)
        elapsed = time.time() - start_time

        text = output.get("choices", [{}])[0].get("text", "").strip()
        usage = output.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        tokens_per_second = tokens_used / elapsed if elapsed > 0 else 0

        logger.debug(
            "Inference: %d tokens in %.2fs (%.1f t/s)",
            tokens_used,
            elapsed,
            tokens_per_second,
        )

        return {
            "text": text,
            "tokens_used": tokens_used,
            "tokens_per_second": tokens_per_second,
            "elapsed_seconds": elapsed,
        }

    def _generate_stream(
        self, params: Dict[str, Any], start_time: float
    ) -> Generator[str, None, None]:
        """Stream tokens one at a time.

        Yields:
            Text chunks as they are generated.
        """
        stream = self._model.create_completion(**params, stream=True)
        for chunk in stream:
            text = chunk.get("choices", [{}])[0].get("text", "")
            if text:
                yield text

    def extract_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Generate and parse JSON output from the LLM.

        Args:
            prompt: User input prompt.
            system_prompt: System instruction.
            max_retries: Number of retries on JSON parse failure.

        Returns:
            Parsed JSON dict.

        Raises:
            LLMError: If JSON parsing fails after max_retries.
        """
        last_error = ""
        for attempt in range(max_retries):
            try:
                result = self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.2 if attempt > 0 else config.llm.temperature,
                )
                text = result["text"]

                # Try to extract JSON from the response
                json_str = self._extract_json_string(text)
                parsed = json.loads(json_str)
                return parsed

            except json.JSONDecodeError as e:
                last_error = str(e)
                logger.warning(
                    "JSON parse failed (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries,
                    e,
                )
                continue

        raise LLMError(
            f"Failed to generate valid JSON after {max_retries} attempts: {last_error}",
        )

    def _extract_json_string(self, text: str) -> str:
        """Extract JSON string from LLM output.

        Handles markdown code blocks and leading/trailing text.

        Args:
            text: Raw LLM output.

        Returns:
            Cleaned JSON string.
        """
        # Remove markdown code block fences
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start : end + 1]

        # For JSON arrays
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            return text[start : end + 1]

        return text.strip()
