"""Text preprocessing and chunking for LLM processing."""

import math
import re
from typing import List

from src.config import config
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class TextProcessor:
    """Clean, normalize, and chunk text for LLM processing."""

    def __init__(self) -> None:
        self.chunk_size = config.chunking.chunk_size_tokens
        self.chunk_overlap = config.chunking.chunk_overlap_tokens

    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing artifacts.

        Removes headers, footers, excessive whitespace, and normalizes
        Unicode characters.

        Args:
            text: Raw extracted text.

        Returns:
            Cleaned text.
        """
        if not text:
            return ""

        # Remove page numbers (common patterns)
        text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

        # Remove headers/footers (short lines at start/end of pages)
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip very short lines that look like page numbers or headers
            if stripped and len(stripped) < 5 and stripped.isdigit():
                continue
            cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)

        # Normalize whitespace
        text = re.sub(r" +", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Normalize Unicode (NFKC normalization)
        import unicodedata

        text = unicodedata.normalize("NFKC", text)

        # Remove null bytes and control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

        # Replace special whitespace characters
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        return text.strip()

    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in text.

        Uses a rough heuristic: 1 token ≈ 4 characters for English text.

        Args:
            text: Input text.

        Returns:
            Estimated token count.
        """
        return len(text) // 4

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks for LLM processing.

        Chunks are split at paragraph boundaries when possible, with
        configurable token size and overlap.

        Args:
            text: Cleaned text to chunk.

        Returns:
            List of text chunks.
        """
        if not text:
            return []

        # Split into paragraphs first
        paragraphs = re.split(r"\n\n+", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_tokens = 0

        for paragraph in paragraphs:
            para_tokens = self._estimate_tokens(paragraph)

            # If single paragraph exceeds chunk size, split it
            if para_tokens > self.chunk_size:
                # Flush current chunk first
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split large paragraph into smaller pieces
                sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                temp_chunk: List[str] = []
                temp_tokens = 0

                for sentence in sentences:
                    sent_tokens = self._estimate_tokens(sentence)
                    if temp_tokens + sent_tokens > self.chunk_size:
                        if temp_chunk:
                            chunks.append(" ".join(temp_chunk))
                        # Keep overlap by retaining last sentences
                        overlap_count = max(
                            1, int(len(temp_chunk) * (self.chunk_overlap / self.chunk_size))
                        )
                        temp_chunk = temp_chunk[-overlap_count:] if overlap_count > 0 else []
                        temp_tokens = self._estimate_tokens(" ".join(temp_chunk))

                    temp_chunk.append(sentence)
                    temp_tokens += sent_tokens

                if temp_chunk:
                    chunks.append(" ".join(temp_chunk))
                continue

            # Check if adding this paragraph would exceed chunk size
            if current_tokens + para_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))

                # Keep overlap paragraphs
                if self.chunk_overlap > 0 and len(current_chunk) > 1:
                    overlap_paras = max(
                        1, int(len(current_chunk) * (self.chunk_overlap / self.chunk_size))
                    )
                    current_chunk = current_chunk[-overlap_paras:]
                    current_tokens = self._estimate_tokens("\n\n".join(current_chunk))
                else:
                    current_chunk = []
                    current_tokens = 0

            current_chunk.append(paragraph)
            current_tokens += para_tokens

        # Add final chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        logger.info(
            "Text split into %d chunks (size=%d, overlap=%d)",
            len(chunks),
            self.chunk_size,
            self.chunk_overlap,
        )
        return chunks

    def estimate_chunks(self, text: str) -> int:
        """Estimate number of chunks without actually chunking.

        Useful for progress reporting.

        Args:
            text: Input text.

        Returns:
            Estimated number of chunks.
        """
        total_tokens = self._estimate_tokens(text)
        if total_tokens <= self.chunk_size:
            return 1
        effective = self.chunk_size - self.chunk_overlap
        return math.ceil(total_tokens / effective)
