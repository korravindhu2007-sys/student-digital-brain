from __future__ import annotations

import fitz

from neuronote.api import generate_quiz, generate_revision_plan, process_document, search_all
from neuronote.database import reset_database


def test_end_to_end_pdf_pipeline(tmp_path):
    db_path = tmp_path / "neuronote.db"
    pdf_path = tmp_path / "dbms.pdf"
    reset_database(db_path)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "DBMS normalization removes redundancy. BCNF is a database normal form.")
    doc.save(pdf_path)
    doc.close()

    document = process_document(pdf_path, metadata={"subject": "DBMS", "topic": "Normalization"}, db_path=db_path)
    search = search_all(keyword="BCNF", db_path=db_path)
    quiz = generate_quiz(question_count=20, db_path=db_path)
    revision = generate_revision_plan(db_path=db_path)

    assert document["ok"]
    assert search[0]["present"]
    assert len(quiz) == 20
    assert revision["important_topics"]
