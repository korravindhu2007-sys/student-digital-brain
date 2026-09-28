"""Full-text search engine for NeuroNote using SQLite FTS5."""

from typing import Any, Dict, List, Optional

from src.config import config
from src.database.connection import get_db
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class SearchEngine:
    """Full-text search across documents and definitions.

    Uses SQLite FTS5 for fast, ranked search results.
    """

    def search(
        self,
        query: str,
        search_type: str = "all",
        subject_id: Optional[int] = None,
        file_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Search across documents and definitions.

        Args:
            query: Search query string.
            search_type: 'all', 'documents', 'definitions', or 'questions'.
            subject_id: Optional subject filter.
            file_type: Optional file type filter.
            limit: Maximum results (default from config).

        Returns:
            Dict with 'results' list and 'total' count.
        """
        if not query or not query.strip():
            return {"results": [], "total": 0, "query": query}

        limit = limit or config.search.max_results
        results: List[Dict[str, Any]] = []

        if search_type in ("all", "documents"):
            results.extend(self._search_documents(query, subject_id, file_type, limit))

        if search_type in ("all", "definitions"):
            results.extend(self._search_definitions(query, subject_id, limit))

        if search_type in ("all", "questions"):
            results.extend(self._search_questions(query, subject_id, limit))

        # Sort by rank (higher is better)
        results.sort(key=lambda x: x.get("rank", 0), reverse=True)

        return {
            "results": results[:limit],
            "total": len(results),
            "query": query,
        }

    def _search_documents(
        self,
        query: str,
        subject_id: Optional[int],
        file_type: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search documents using FTS5.

        Args:
            query: Search query.
            subject_id: Optional subject filter.
            file_type: Optional file type filter.
            limit: Maximum results.

        Returns:
            List of result dicts.
        """
        try:
            fts_query = self._build_fts_query(query)

            sql = """
                SELECT
                    d.id, d.title, d.file_type, d.created_at,
                    s.name as subject_name,
                    snippet(documents_fts, 1, '<mark>', '</mark>', '...', 20) as snippet,
                    rank
                FROM documents_fts
                JOIN documents d ON documents_fts.rowid = d.id
                LEFT JOIN subjects s ON d.subject_id = s.id
                WHERE documents_fts MATCH ?
            """
            params: List[Any] = [fts_query]

            if subject_id is not None:
                sql += " AND d.subject_id = ?"
                params.append(subject_id)
            if file_type:
                sql += " AND d.file_type = ?"
                params.append(file_type)

            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)

            with get_db() as conn:
                cursor = conn.execute(sql, params)
                results = []
                for row in cursor.fetchall():
                    results.append(
                        {
                            "type": "document",
                            "id": row["id"],
                            "title": row["title"],
                            "file_type": row["file_type"],
                            "subject": row["subject_name"],
                            "snippet": row["snippet"],
                            "rank": row["rank"],
                            "created_at": row["created_at"],
                        }
                    )
                return results

        except Exception as e:
            logger.error("Document search failed: %s", e)
            return []

    def _search_definitions(
        self,
        query: str,
        subject_id: Optional[int],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search definitions (concepts) by term or content.

        Args:
            query: Search query.
            subject_id: Optional subject filter.
            limit: Maximum results.

        Returns:
            List of result dicts.
        """
        try:
            pattern = f"%{query}%"
            sql = """
                SELECT def.*, s.name as subject_name, t.name as topic_name
                FROM definitions def
                LEFT JOIN subjects s ON def.subject_id = s.id
                LEFT JOIN topics t ON def.topic_id = t.id
                WHERE (def.term LIKE ? OR def.definition LIKE ?)
            """
            params: List[Any] = [pattern, pattern]

            if subject_id is not None:
                sql += " AND def.subject_id = ?"
                params.append(subject_id)

            sql += " ORDER BY def.importance DESC, def.term LIMIT ?"
            params.append(limit)

            with get_db() as conn:
                cursor = conn.execute(sql, params)
                results = []
                for row in cursor.fetchall():
                    results.append(
                        {
                            "type": "definition",
                            "id": row["id"],
                            "title": row["term"],
                            "content": row["definition"],
                            "subject": row["subject_name"],
                            "topic": row["topic_name"],
                            "importance": row["importance"],
                            "rank": 1.0 if row["importance"] == "high" else 0.8,
                        }
                    )
                return results

        except Exception as e:
            logger.error("Definition search failed: %s", e)
            return []

    def _search_questions(
        self,
        query: str,
        subject_id: Optional[int],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Search questions by text.

        Args:
            query: Search query.
            subject_id: Optional subject filter.
            limit: Maximum results.

        Returns:
            List of result dicts.
        """
        try:
            pattern = f"%{query}%"
            sql = """
                SELECT q.*, s.name as subject_name
                FROM questions q
                LEFT JOIN subjects s ON q.subject_id = s.id
                WHERE q.question_text LIKE ? OR q.answer LIKE ?
            """
            params: List[Any] = [pattern, pattern]

            if subject_id is not None:
                sql += " AND q.subject_id = ?"
                params.append(subject_id)

            sql += " ORDER BY q.difficulty, q.created_at DESC LIMIT ?"
            params.append(limit)

            with get_db() as conn:
                cursor = conn.execute(sql, params)
                results = []
                for row in cursor.fetchall():
                    results.append(
                        {
                            "type": "question",
                            "id": row["id"],
                            "title": row["question_text"][:100],
                            "content": row["answer"],
                            "subject": row["subject_name"],
                            "difficulty": row["difficulty"],
                            "rank": 0.9,
                        }
                    )
                return results

        except Exception as e:
            logger.error("Question search failed: %s", e)
            return []

    def _build_fts_query(self, query: str) -> str:
        """Build an FTS5 query string.

        Converts user query to FTS5 syntax with prefix matching.

        Args:
            query: User search query.

        Returns:
            FTS5 query string.
        """
        # Split into words and add prefix matching
        words = query.strip().split()
        fts_terms = []
        for word in words:
            # Remove special FTS5 characters
            word = word.replace('"', '""')
            fts_terms.append(f'"{word}"*')

        return " ".join(fts_terms)

    def get_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for a search prefix.

        Args:
            prefix: Search prefix.
            limit: Maximum suggestions.

        Returns:
            List of suggestion strings.
        """
        try:
            pattern = f"{prefix}%"
            with get_db() as conn:
                cursor = conn.execute(
                    """SELECT term FROM definitions
                       WHERE term LIKE ?
                       ORDER BY importance DESC, term
                       LIMIT ?""",
                    (pattern, limit),
                )
                return [row["term"] for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Failed to get suggestions: %s", e)
            return []

    def get_related_terms(self, term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find terms related to a given term.

        Args:
            term: Source term.
            limit: Maximum results.

        Returns:
            List of related term dicts.
        """
        try:
            with get_db() as conn:
                cursor = conn.execute(
                    """SELECT d2.term, d2.definition, kl.relationship_type, kl.weight
                       FROM knowledge_links kl
                       JOIN definitions d1 ON kl.source_concept_id = d1.id
                       JOIN definitions d2 ON kl.target_concept_id = d2.id
                       WHERE d1.term = ?
                       UNION
                       SELECT d1.term, d1.definition, kl.relationship_type, kl.weight
                       FROM knowledge_links kl
                       JOIN definitions d1 ON kl.source_concept_id = d1.id
                       JOIN definitions d2 ON kl.target_concept_id = d2.id
                       WHERE d2.term = ?
                       ORDER BY kl.weight DESC
                       LIMIT ?""",
                    (term, term, limit),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Failed to get related terms: %s", e)
            return []
