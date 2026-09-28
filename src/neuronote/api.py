from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .database import (
    DatabaseManager,
    dashboard_counts,
    get_document,
    get_document_by_hash,
    get_search_cache,
    latest_quiz_record,
    latest_revision_record,
    list_documents,
    save_quiz_record,
    save_revision_record,
    save_search_cache,
)
from .ingestion import create_semantic_chunks, extract_pdf_pages, persist_input_file
from .logging_config import get_logger
from .ollama import OllamaService, ollama_status

logger = get_logger(__name__)


def process_document(
    file: Any,
    metadata: dict[str, object] | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    metadata = dict(metadata or {})
    manager = DatabaseManager(db_path)
    try:
        original_name, source_path = persist_input_file(file)
        source_name = source_path.name
        if source_path.suffix.lower() != ".pdf":
            return _disabled_result(source_name, "NeuroNote accepts study PDFs only in this phase.")

        pdf_hash = _file_hash(source_path)
        cached = get_document_by_hash(pdf_hash, db_path=db_path)
        if cached and str(cached.get("raw_text", "")).strip():
            return _document_result(cached, status="cached", cache_hit=True, db_path=db_path)

        pages = extract_pdf_pages(source_path)
        raw_text = "\n\n".join(str(page.get("text", "")) for page in pages if str(page.get("text", "")).strip())
        if not raw_text.strip():
            return _disabled_result(source_name, "Could not extract text from PDF. Try OCR-ready scans or text PDFs.")

        chunks = create_semantic_chunks(pages)
        structured = {
            "source_name": source_name,
            "source_path": str(source_path),
            "source_type": "pdf",
            "pdf_hash": pdf_hash,
            "subject": str(metadata.get("subject", "General")),
            "topic": str(metadata.get("topic", "General")),
            "summary": _summary(raw_text),
            "pages": pages,
            "raw_text": raw_text,
            "engine": "offline-extraction",
        }
        document_id = manager.insert_document(
            filename=source_name,
            file_hash=pdf_hash,
            pages=len(pages),
            file_path=str(source_path),
            file_size=source_path.stat().st_size,
            subject=str(metadata.get("subject", "General")),
            topic=str(metadata.get("topic", "General")),
            raw_text=raw_text,
            processed=True,
            summary=str(structured["summary"]),
            structured_json=structured,
        )
        subject = str(metadata.get("subject", "General"))
        chapter = str(metadata.get("topic", "General"))
        for chunk in chunks:
            text = str(chunk.get("text", ""))
            manager.insert_chunk(
                document_id=document_id,
                page=int(str(chunk.get("page") or 1)),
                chunk_index=int(str(chunk.get("chunk_index") or 0)),
                text=text,
                embedding_placeholder=str(chunk.get("embedding_placeholder", "")),
                subject=subject,
                chapter=chapter,
                estimated_topic=_estimate_chunk_topic(text, chapter),
            )
        document = get_document(document_id, db_path=db_path) or {}
        result = _document_result(document, status="processed", cache_hit=False, db_path=db_path)
        result["chunk_count"] = len(chunks)
        result["original_name"] = original_name
        return result
    except Exception as exc:
        logger.exception("PDF processing failed")
        return {"ok": False, "status": "failed", "error": str(exc)}


def process_image(file: Any, db_path: Path | None = None) -> dict[str, Any]:
    del db_path
    name = getattr(file, "name", None) or (file.get("name") if isinstance(file, dict) else "image")
    return _disabled_result(str(name), "Image processing is deferred until the next architecture phase.")


def process_audio(file: Any, db_path: Path | None = None) -> dict[str, Any]:
    del db_path
    name = getattr(file, "name", None) or (file.get("name") if isinstance(file, dict) else "audio")
    return _disabled_result(str(name), "Audio processing is deferred until the next architecture phase.")


def search_all(
    query: str | None = None,
    document_ids: list[int] | None = None,
    db_path: Path | None = None,
    keyword: str | None = None,
) -> list[dict[str, Any]]:
    from retrieval import SemanticSearch
    term = (query or keyword or "").strip()
    if not term:
        return [{"present": False, "explanation": "Enter a search term."}]
    results = SemanticSearch(db_path).search(term, document_ids=document_ids, top_k=10)
    if not results:
        return [{"present": False, "explanation": "The uploaded study material does not contain this information."}]
    return [_format_search_result(result) for result in results]


def search_keyword(keyword: str, db_path: Path | None = None) -> list[dict[str, Any]]:
    return search_all(keyword=keyword, db_path=db_path)


def get_dashboard_stats(db_path: Path | None = None) -> dict[str, Any]:
    counts = dashboard_counts(db_path=db_path)
    quiz = latest_quiz_record(db_path=db_path)
    revision = latest_revision_record(db_path=db_path)
    return {
        "metrics": {
            "Uploaded PDFs": str(counts["documents"]),
            "Subjects": str(counts["subjects"]),
            "Topics": str(counts["topics"]),
            "Quiz Generated": str(counts["quizzes"]),
            "Revision Available": "Yes" if revision else "No",
        },
        "counts": counts,
        "ollama": ollama_status(),
        "latest_quiz": quiz,
        "latest_revision": revision,
    }


def get_pdf_options(db_path: Path | None = None) -> dict[str, Any]:
    documents = [row for row in list_documents(db_path=db_path) if row.get("source_type") == "pdf"]
    subjects = sorted({str(row.get("subject", "General")) for row in documents})
    topics_by_subject: dict[str, list[str]] = {}
    for row in documents:
        subject = str(row.get("subject", "General"))
        topic = str(row.get("topic", "General"))
        topics_by_subject.setdefault(subject, [])
        if topic not in topics_by_subject[subject]:
            topics_by_subject[subject].append(topic)
    return {
        "subjects": subjects,
        "topics_by_subject": {key: sorted(values) for key, values in topics_by_subject.items()},
        "documents": documents,
    }


def retrieve_context(
    question: str,
    document_ids: list[int] | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    from retrieval import RetrievalEngine
    return RetrievalEngine(db_path).retrieve_for_chat(question, document_ids=document_ids)


def answer_question(
    question: str,
    document_ids: list[int] | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    term = question.strip()
    if not term:
        return {"ok": False, "answer": "Enter a question.", "sources": []}

    from retrieval import RetrievalEngine
    answer_hash = _response_cache_hash("chat-answer", term, document_ids)
    cached = get_search_cache(answer_hash, db_path=db_path)
    if cached:
        cached["cache_hit"] = True
        return cached

    retrieval = RetrievalEngine(db_path).retrieve_for_chat(term, document_ids=document_ids)
    context = str(retrieval.get("context", "")).strip()
    if not context:
        response = {
            "ok": True,
            "answer": "The uploaded study material does not contain this information.",
            "confidence": 0,
            "sources": [],
            "retrieval": retrieval,
            "cache_hit": False,
        }
        save_search_cache(answer_hash, {"question": term, "document_ids": document_ids or []}, response, db_path)
        return response

    parsed = OllamaService(db_path=db_path).chat(term, context)
    response = _chat_response(term, parsed, retrieval)
    save_search_cache(answer_hash, {"question": term, "document_ids": document_ids or []}, response, db_path)
    return response


def generate_quiz(question_count: int = 20, db_path: Path | None = None) -> list[dict[str, Any]]:
    document = _latest_document(db_path)
    subject = str(document.get("subject", "General")) if document else "General"
    topic = str(document.get("topic", "General")) if document else "General"
    sentences = _sentences(str(document.get("raw_text", "")) if document else "")
    if not sentences:
        sentences = ["The uploaded study material does not contain this information."]
    questions: list[dict[str, Any]] = []
    for index in range(question_count):
        source = sentences[index % len(sentences)]
        answer = _answer_from_sentence(source)
        questions.append(
            {
                "question": f"According to the uploaded study material, what is key point {index + 1}?",
                "options": {"A": answer, "B": "Not stated", "C": "Outside material", "D": "Unrelated detail"},
                "correct_answer": "A",
                "explanation": source,
            }
        )
    save_quiz_record(subject, topic, questions, db_path=db_path, document_id=document.get("id") if document else None)
    return questions


def generate_revision_plan(db_path: Path | None = None) -> dict[str, Any]:
    document = _latest_document(db_path)
    subject = str(document.get("subject", "General")) if document else "General"
    topic = str(document.get("topic", "General")) if document else "General"
    text = str(document.get("raw_text", "")) if document else ""
    topics = _keywords(text, limit=6) or [topic]
    important_topics = [{"title": item, "explanation": _matching_sentence(text, item)} for item in topics]
    plan = {
        "mind_map": {"subject": subject, "chapter": topic, "root": topic, "topics": important_topics},
        "important_topics": important_topics,
        "definitions": [{"term": item, "definition": _matching_sentence(text, item)} for item in topics],
        "study_notes": {"Summary": _summary(text)},
        "question_bank": {"very_short": [], "short": [], "long": []},
    }
    save_revision_record(subject, topic, plan, db_path=db_path, document_id=document.get("id") if document else None)
    return plan


def _document_result(
    document: dict[str, Any],
    status: str,
    cache_hit: bool,
    db_path: Path | None = None,
) -> dict[str, Any]:
    chunks = DatabaseManager(db_path).get_chunks(int(document.get("id") or 0))
    return {
        "ok": True,
        "document_id": document.get("id"),
        "structured_json": _loads_dict(str(document.get("structured_json") or "{}")),
        "status": status,
        "source_name": document.get("filename") or document.get("source_name") or document.get("title"),
        "source_type": "pdf",
        "source_path": document.get("file_path", ""),
        "pdf_hash": document.get("file_hash") or document.get("pdf_hash", ""),
        "extracted_chars": len(str(document.get("raw_text", "")).strip()),
        "page_count": document.get("pages") or document.get("page_count") or 0,
        "chunk_count": len(chunks),
        "image_count": 0,
        "cache_hit": cache_hit,
    }


def _format_chunk_result(chunk: dict[str, Any]) -> dict[str, Any]:
    text = str(chunk.get("text", ""))
    return {
        "present": True,
        "answer": text[:500],
        "explanation": text,
        "source_page": chunk.get("page") or chunk.get("page_number"),
        "source_paragraph": chunk.get("chunk_index"),
        "confidence": 85,
        "text": text,
    }


def _format_search_result(result: dict[str, Any]) -> dict[str, Any]:
    text = str(result.get("paragraph", ""))
    return {
        "present": True,
        "answer": text[:500],
        "explanation": text,
        "source_page": result.get("page_number"),
        "source_paragraph": result.get("chunk_number"),
        "source_filename": result.get("source_filename"),
        "confidence": result.get("confidence", 0),
        "matched_keywords": result.get("matched_keywords", []),
        "title": result.get("title", ""),
        "text": text,
    }


def _chat_response(question: str, parsed: dict[str, Any] | None, retrieval: dict[str, Any]) -> dict[str, Any]:
    chunks = retrieval.get("chunks", [])
    fallback_answer = _fallback_answer(chunks)
    answer = fallback_answer
    confidence = 0
    related_topics: list[str] = []
    suggested_followups: list[str] = []
    if isinstance(parsed, dict):
        answer = str(parsed.get("answer") or fallback_answer)
        confidence = int(parsed.get("confidence") or 0)
        related_topics = [str(item) for item in parsed.get("related_topics", []) if item]
        suggested_followups = [str(item) for item in parsed.get("suggested_followups", []) if item]
    return {
        "ok": True,
        "question": question,
        "answer": answer,
        "confidence": confidence,
        "related_topics": related_topics,
        "suggested_followups": suggested_followups,
        "sources": retrieval.get("references", []),
        "retrieval": retrieval,
        "cache_hit": False,
    }


def _fallback_answer(chunks: object) -> str:
    if not isinstance(chunks, list) or not chunks:
        return "The uploaded study material does not contain this information."
    first = chunks[0]
    if not isinstance(first, dict):
        return "The uploaded study material does not contain this information."
    return str(first.get("text", ""))[:700] or "The uploaded study material does not contain this information."


def _estimate_chunk_topic(text: str, default_topic: str) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text)
    stop = {"this", "that", "with", "from", "into", "uses", "have", "were", "will", "only"}
    counts: dict[str, int] = {}
    for word in words:
        key = word.lower()
        if key in stop:
            continue
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return default_topic
    best = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return best.title()


def _response_cache_hash(purpose: str, question: str, document_ids: list[int] | None) -> str:
    payload = {"purpose": purpose, "question": question.strip().lower(), "document_ids": sorted(document_ids or [])}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _latest_document(db_path: Path | None = None) -> dict[str, Any] | None:
    documents = list_documents(db_path=db_path)
    return documents[0] if documents else None


def _disabled_result(source_name: str, error: str) -> dict[str, Any]:
    return {"ok": False, "status": "rejected", "source_name": source_name, "error": error}


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _loads_dict(raw: str) -> dict[str, Any]:
    try:
        loaded = __import__("json").loads(raw)
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _summary(text: str) -> str:
    return " ".join(_sentences(text)[:3])[:700]


def _keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text)
    seen: list[str] = []
    for word in words:
        label = word.strip().title()
        if label.lower() in {"this", "that", "with", "from", "into", "uses"}:
            continue
        if label not in seen:
            seen.append(label)
        if len(seen) >= limit:
            break
    return seen


def _matching_sentence(text: str, keyword: str) -> str:
    for sentence in _sentences(text):
        if keyword.lower() in sentence.lower():
            return sentence
    return _summary(text) or "The uploaded study material does not contain this information."


def _answer_from_sentence(sentence: str) -> str:
    words = sentence.split()
    return " ".join(words[: min(10, len(words))]) or "The uploaded study material does not contain this information."
