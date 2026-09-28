# Master Prompt 2 Implementation Plan

## Part 2.1 - UI Architecture
- [ ] Create styles/theme.py and styles/custom_css.py
- [ ] Create components: topbar.py, pdf_viewer.py, chat_box.py, upload_widget.py, status_card.py, empty_state.py, loading.py
- [ ] Update components/notifications.py to use toast notifications
- [ ] Rewrite components/sidebar.py with logo, navigation, offline status, ollama model, storage, database status
- [ ] Rewrite components/cards.py with modern card designs
- [ ] Rewrite pages/Dashboard.py with stats cards, recent documents, activity, quick actions, empty state
- [ ] Rewrite pages/Upload.py with drag & drop, processing stages, progress bars, document details
- [ ] Rewrite pages/chat.py → pages/AI_Chat.py with three-panel chat layout
- [ ] Update app.py to register all new pages

## Part 2.2 - AI Chat
- [ ] Create pages/AI_Chat.py with three-panel layout (history, chat, sources)
- [ ] Implement conversation memory with session management
- [ ] Add source citations and PDF viewer integration
- [ ] Add follow-up buttons and related topics
- [ ] Add chat features: export, pin, rename, delete conversations
- [ ] Add keyboard shortcuts

## Part 2.3 - Study Mode, Flash Cards, Formula Sheet, Settings
- [ ] Rewrite pages/Study_Mode.py with TOC sidebar, expandable notes, interactive features
- [ ] Rewrite pages/Flash_Cards.py with flip animation, progress, filters, shuffle
- [ ] Rewrite pages/Formula_Sheet.py with search, cards, filters, copy
- [ ] Rewrite pages/Settings.py with theme, ollama, cache, status, backup
- [ ] Add responsive design across all pages
- [ ] Add animations and transitions
- [ ] Final integration testing