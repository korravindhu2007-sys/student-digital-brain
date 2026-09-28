#!/usr/bin/env python3
"""Example usage of NeuroNote backend API.

This script demonstrates how to use the NeuroNote API
to process documents, search, and generate quizzes.
"""

from pathlib import Path

from src.api import api
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


def main():
    """Run example workflow."""
    print("=" * 60)
    print("NeuroNote Backend - Example Usage")
    print("=" * 60)

    # Initialize the application
    print("\n1. Initializing application...")
    result = api.initialize()
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")

    # Get dashboard stats
    print("\n2. Getting dashboard statistics...")
    stats = api.get_dashboard_stats()
    print(f"   Total documents: {stats['documents']['total']}")
    print(f"   Subjects: {stats['subjects']}")

    # List subjects
    print("\n3. Listing subjects...")
    subjects = api.get_subjects()
    if subjects:
        for subject in subjects:
            print(f"   - {subject['name']} ({subject['document_count']} docs)")
    else:
        print("   No subjects found. Upload a document to get started!")

    # Example: Process a text file (if it exists)
    example_file = Path("examples/sample_notes.txt")
    if example_file.exists():
        print(f"\n4. Processing example file: {example_file}")
        try:
            result = api.upload_and_process(
                file_path=str(example_file),
                subject_name="Example Subject",
            )
            print(f"   Document ID: {result['document_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Concepts extracted: {result.get('concepts_extracted', 0)}")
        except Exception as e:
            print(f"   Error: {e}")
    else:
        print(f"\n4. Skipping file processing (example file not found: {example_file})")
        print("   To test, create a file at examples/sample_notes.txt")

    # Example: Search (if documents exist)
    if stats["documents"]["total"] > 0:
        print("\n5. Searching for 'cell division'...")
        search_results = api.search(query="cell division", limit=5)
        print(f"   Found {search_results['total']} results")
        for idx, result in enumerate(search_results["results"][:3], 1):
            print(f"   {idx}. [{result['type']}] {result['title']}")
    else:
        print("\n5. Skipping search (no documents in database)")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
