from neuronote.database import dashboard_counts, list_concepts, reset_database, save_document_record, search_concepts


def test_save_document_and_search(tmp_path):
    db_path = tmp_path / "neuronote.db"
    reset_database(db_path)

    document_id = save_document_record(
        {
            "source_name": "biology.txt",
            "source_type": "text",
            "subject": "Biology",
            "topic": "Cells",
            "raw_text": "Mitochondria produce energy.",
            "concepts": [
                {
                    "concept": "Mitochondria",
                    "definition": "Organelles that produce energy.",
                    "subject": "Biology",
                    "topic": "Cells",
                    "importance": "high",
                    "related_concepts": ["Energy"],
                }
            ],
        },
        db_path=db_path,
    )

    assert document_id == 1
    assert len(list_concepts(db_path)) == 1
    assert search_concepts("subject", "Biology", db_path)[0]["concept"] == "Mitochondria"
    assert dashboard_counts(db_path)["documents"] == 1
