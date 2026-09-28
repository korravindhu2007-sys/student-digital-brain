"""Text chunking utilities for semantic search."""

from __future__ import annotations

import re
from typing import Any


class SemanticChunker:
    """Wrapper for semantic text chunking."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, pages: Any | None = None) -> list[dict[str, Any]]:
        return chunk_text_semantic(text, max_chunk_size=self.chunk_size, overlap=self.chunk_overlap)


def chunk_text_semantic(text: str, max_chunk_size: int = 800, overlap: int = 100) -> list[dict[str, Any]]:
    """Split text into semantic chunks with overlap.

    Args:
        text: Input text to chunk.
        max_chunk_size: Maximum characters per chunk.
        overlap: Overlap between chunks in characters.

    Returns:
        List of chunk dicts with text, page_number, section_heading, token_count.
    """
    if not text or not text.strip():
        return []

    # Clean text
    clean = text.replace("\r\n", "\n").strip()
    lines = [line.strip() for line in clean.splitlines() if line.strip()]

    current_chunk: list[str] = []
    current_size = 0
    chunks: list[dict[str, Any]] = []
    chunk_index = 0
    page_number = 1
    section_heading = ""

    for line in lines:
        # Check for page markers (simple heuristic)
        if re.match(r"^Page \d+$", line, re.IGNORECASE):
            page_match = re.search(r"\d+", line)
            if page_match:
                page_number = int(page_match.group())
            continue

        # Check for section headings
        if re.match(r"^(\d+\.)*\d*\s+[A-Z][A-Za-z\s]+$", line):
            section_heading = line

        line_size = len(line) + 1  # +1 for newline

        if current_size + line_size > max_chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "page_number": page_number,
                "section_heading": section_heading,
                "token_count": len(chunk_text.split()),
                "chunk_index": chunk_index,
            })
            chunk_index += 1

            # Keep overlap from end of current chunk
            if overlap > 0 and current_chunk:
                overlap_lines = []
                overlap_size = 0
                for prev_line in reversed(current_chunk):
                    if overlap_size + len(prev_line) <= overlap:
                        overlap_lines.insert(0, prev_line)
                        overlap_size += len(prev_line) + 1
                    else:
                        break
                current_chunk = overlap_lines
                current_size = overlap_size
            else:
                current_chunk = []
                current_size = 0

        current_chunk.append(line)
        current_size += line_size

    # Add final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({
            "text": chunk_text,
            "page_number": page_number,
            "section_heading": section_heading,
            "token_count": len(chunk_text.split()),
            "chunk_index": chunk_index,
        })

    return chunks


def chunk_text_by_paragraphs(text: str, max_chunk_size: int = 1000) -> list[dict[str, Any]]:
    """Split text by paragraphs.

    Args:
        text: Input text.
        max_chunk_size: Maximum chunk size.

    Returns:
        List of chunk dicts.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[dict[str, Any]] = []
    current: list[str] = []
    current_size = 0
    chunk_index = 0

    for para in paragraphs:
        para_size = len(para)

        if current_size + para_size > max_chunk_size and current:
            chunk_text = "\n\n".join(current)
            chunks.append({
                "text": chunk_text,
                "page_number": 1,
                "section_heading": "",
                "token_count": len(chunk_text.split()),
                "chunk_index": chunk_index,
            })
            chunk_index += 1
            current = []
            current_size = 0

        current.append(para)
        current_size += para_size + 2

    if current:
        chunk_text = "\n\n".join(current)
        chunks.append({
            "text": chunk_text,
            "page_number": 1,
            "section_heading": "",
            "token_count": len(chunk_text.split()),
            "chunk_index": chunk_index,
        })

    return chunks