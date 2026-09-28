#!/usr/bin/env python3
"""Quick test to verify NeuroNote application loads correctly."""

import sys
from pathlib import Path

# Use script location for paths (matches app.py behavior)
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

# Add ROOT_DIR first so packages like 'services' and 'pages' are found
# Then add SRC_DIR for 'neuronote', 'src.database', etc.
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(1, str(SRC_DIR))

print("=" * 50)
print("NeuroNote Application Test")
print("=" * 50)
print(f"ROOT_DIR: {ROOT_DIR}")
print(f"SRC_DIR: {SRC_DIR}")
print(f"sys.path[0:3]: {sys.path[0:3]}")

try:
    # Test imports - ROOT_DIR packages first
    from services.backend import get_app_status
    print("[PASS] services.backend imports")
    
    from pages.dashboard import render_dashboard
    print("[PASS] pages.dashboard imports")
    
    from pages.upload import render_upload
    print("[PASS] pages.upload imports")
    
    from pages.chat import render_chat
    print("[PASS] pages.chat imports")
    
    from pages.study_mode import render_study_mode
    print("[PASS] pages.study_mode imports")
    
    from pages.flashcards import render_flashcards
    print("[PASS] pages.flashcards imports")
    
    from pages.highlights import render_highlights
    print("[PASS] pages.highlights imports")
    
    from pages.formulas import render_formulas
    print("[PASS] pages.formulas imports")
    
    from pages.settings import render_settings
    print("[PASS] pages.settings imports")
    
    # Test SRC_DIR packages
    from src.database.schema import initialize_database
    print("[PASS] src.database.schema imports")
    
    from src.neuronote.prompts import CHAT_PROMPT
    print("[PASS] src.neuronote.prompts imports")
    
    from src.utils.chunking import chunk_text_semantic
    chunks = chunk_text_semantic("test " * 100, 20, 5)
    print(f"[PASS] chunking works: {len(chunks)} chunks")
    
    # Verify app status
    status = get_app_status()
    print(f"[INFO] App mode: {status.get('mode')}")
    
    print("")
    print("=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
    print("\nRun: streamlit run app.py")
    
except Exception as e:
    print(f"\n[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)