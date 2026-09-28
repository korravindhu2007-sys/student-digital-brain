"""Knowledge graph construction using NetworkX."""

from typing import Any, Dict, List, Optional, Tuple

from src.config import config
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class KnowledgeGraphBuilder:
    """Build and manage a knowledge graph connecting concepts.

    Uses NetworkX for graph construction and TF-IDF for similarity-based
    relationship detection.
    """

    def __init__(self) -> None:
        self._graph = None
        self.similarity_threshold = config.knowledge_graph.similarity_threshold

    @property
    def _graph_available(self) -> bool:
        """Check if NetworkX is available."""
        import importlib.util

        return importlib.util.find_spec("networkx") is not None

    def _get_graph(self):
        """Get or initialize the NetworkX graph."""
        if self._graph is None:
            import networkx as nx

            self._graph = nx.Graph()
        return self._graph

    def add_concept(
        self,
        concept_id: int,
        term: str,
        definition: str,
        subject: str = "",
        importance: str = "medium",
    ) -> None:
        """Add a concept node to the graph.

        Args:
            concept_id: Unique concept identifier.
            term: Concept term.
            definition: Concept definition.
            subject: Subject area.
            importance: Importance level.
        """
        graph = self._get_graph()
        graph.add_node(
            concept_id,
            term=term,
            definition=definition,
            subject=subject,
            importance=importance,
        )

    def add_relationship(
        self,
        source_id: int,
        target_id: int,
        relationship_type: str = "related_to",
        weight: float = 1.0,
    ) -> None:
        """Add an edge between two concepts.

        Args:
            source_id: Source concept ID.
            target_id: Target concept ID.
            relationship_type: Type of relationship.
            weight: Relationship strength.
        """
        graph = self._get_graph()
        if graph.has_node(source_id) and graph.has_node(target_id):
            graph.add_edge(
                source_id,
                target_id,
                relationship=relationship_type,
                weight=weight,
            )

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts using TF-IDF.

        Args:
            text1: First text (term + definition).
            text2: Second text.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            logger.warning("scikit-learn not installed; using fallback similarity")
            return self._fallback_similarity(text1, text2)

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=1000,
        )
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(similarity[0][0])

    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity when scikit-learn is not available.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        import re

        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0

    def find_related_concepts(
        self, new_concept: Dict[str, Any], existing_concepts: List[Dict[str, Any]]
    ) -> List[Tuple[int, str, float]]:
        """Find existing concepts related to a new concept.

        Args:
            new_concept: Dict with 'id', 'term', 'definition'.
            existing_concepts: List of existing concept dicts.

        Returns:
            List of (concept_id, relationship_type, weight) tuples.
        """
        new_text = f"{new_concept.get('term', '')} {new_concept.get('definition', '')}"
        related: List[Tuple[int, str, float]] = []

        for existing in existing_concepts:
            existing_text = f"{existing.get('term', '')} {existing.get('definition', '')}"
            similarity = self.compute_similarity(new_text, existing_text)

            if similarity >= self.similarity_threshold:
                # Determine relationship type based on similarity
                if similarity >= 0.7:
                    rel_type = "related_to"
                elif new_concept.get("term", "").lower() in existing_text.lower():
                    rel_type = "is_a"
                elif existing.get("term", "").lower() in new_text.lower():
                    rel_type = "example_of"
                else:
                    rel_type = "related_to"

                related.append((existing["id"], rel_type, similarity))

        return sorted(related, key=lambda x: x[2], reverse=True)

    def link_concepts_by_related_field(
        self,
        new_concept: Dict[str, Any],
        existing_concepts: List[Dict[str, Any]],
    ) -> List[Tuple[int, str, float]]:
        """Link concepts based on explicit related_concepts field.

        Args:
            new_concept: Concept with 'related_concepts' list.
            existing_concepts: Existing concepts to match against.

        Returns:
            List of (concept_id, relationship_type, weight) tuples.
        """
        related_terms = new_concept.get("related_concepts", [])
        if not related_terms:
            return []

        links: List[Tuple[int, str, float]] = []
        new_term_lower = new_concept.get("term", "").lower()

        for existing in existing_concepts:
            existing_term = existing.get("term", "").lower()
            if existing_term in [r.lower() for r in related_terms]:
                weight = 1.0 if existing_term != new_term_lower else 0.0
                if weight > 0:
                    links.append((existing["id"], "related_to", weight))

        return links

    def build_from_database(
        self,
        definitions: List[Dict[str, Any]],
        existing_links: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build the full knowledge graph from database records.

        Args:
            definitions: List of definition dicts from database.
            existing_links: Pre-existing links to include.

        Returns:
            Dict with 'nodes' and 'edges' lists for visualization.
        """
        graph = self._get_graph()

        # Add all concept nodes
        for defn in definitions:
            self.add_concept(
                concept_id=defn["id"],
                term=defn.get("term", ""),
                definition=defn.get("definition", ""),
                subject=defn.get("subject_name", ""),
                importance=defn.get("importance", "medium"),
            )

        # Add existing links from database
        if existing_links:
            for link in existing_links:
                self.add_relationship(
                    source_id=link["source_concept_id"],
                    target_id=link["target_concept_id"],
                    relationship_type=link.get("relationship_type", "related_to"),
                    weight=link.get("weight", 1.0),
                )

        # Auto-link similar concepts
        concept_list = [
            {
                "id": n,
                "term": graph.nodes[n].get("term", ""),
                "definition": graph.nodes[n].get("definition", ""),
            }
            for n in graph.nodes()
        ]

        for i, c1 in enumerate(concept_list):
            for c2 in concept_list[i + 1 :]:
                if not graph.has_edge(c1["id"], c2["id"]):
                    similarity = self.compute_similarity(
                        f"{c1['term']} {c1['definition']}",
                        f"{c2['term']} {c2['definition']}",
                    )
                    if similarity >= self.similarity_threshold:
                        self.add_relationship(
                            source_id=c1["id"],
                            target_id=c2["id"],
                            relationship_type="related_to",
                            weight=similarity,
                        )

        return self.export_visualization()

    def export_visualization(self) -> Dict[str, Any]:
        """Export graph data for frontend visualization.

        Returns:
            Dict with 'nodes' and 'edges' lists.
        """
        graph = self._get_graph()
        nodes = [
            {
                "id": n,
                "term": data.get("term", ""),
                "subject": data.get("subject", ""),
                "importance": data.get("importance", "medium"),
            }
            for n, data in graph.nodes(data=True)
        ]
        edges = [
            {
                "source": u,
                "target": v,
                "relationship": data.get("relationship", "related_to"),
                "weight": data.get("weight", 1.0),
            }
            for u, v, data in graph.edges(data=True)
        ]
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "density": round(
                    graph.number_of_edges() / (graph.number_of_nodes() * (graph.number_of_nodes() - 1) / 2)
                    if graph.number_of_nodes() > 1
                    else 0,
                    4,
                ),
            },
        }

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics.

        Returns:
            Dict with node_count, edge_count, density, etc.
        """
        import networkx as nx

        graph = self._get_graph()
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "density": round(nx.density(graph), 4) if self._graph_available else 0,
        }
