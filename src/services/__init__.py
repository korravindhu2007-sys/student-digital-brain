"""Services package for NeuroNote."""

from __future__ import annotations

from src.services.cache_service import get_cache_service
from src.services.chat_service import ChatService, get_chat_service
from src.services.dashboard_service import DashboardService, get_dashboard_service
from src.services.document_service import (
    DocumentMetadata,
    DocumentService,
    ProcessingResult,
    get_document_service,
)
from src.services.study_service import StudyNotes, StudyService, get_study_service

__all__ = [
    # Document
    "DocumentService",
    "DocumentMetadata",
    "ProcessingResult",
    "get_document_service",
    # Chat
    "ChatService",
    "get_chat_service",
    # Study
    "StudyService",
    "StudyNotes",
    "get_study_service",
    # Cache
    "get_cache_service",
    # Dashboard
    "DashboardService",
    "get_dashboard_service",
]
