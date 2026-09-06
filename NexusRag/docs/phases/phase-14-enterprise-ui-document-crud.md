# Phase 14 — Enterprise UI Redesign + Document Management CRUD

## 1. Executive Summary

Phase 14 delivers a comprehensive visual redesign and functional expansion of **NexusRAG**, transforming it from a dark-themed developer prototype into a modern, light-themed enterprise AI knowledge assistant inspired by the clean aesthetics of Linear, Notion, and modern SaaS dashboards. 

In addition to visual polish, this phase resolves severe component and layout bugs present in earlier iterations (specifically the detached chat input button and document table column overlap) while introducing full-stack **Document Management CRUD operations** (`GET`, `DELETE`, `PUT`) backed by ChromaDB vector metadata filtering, atomic Redis query cache invalidation, and accessible React modals.

All existing RAG retrieval, generation, streaming, conversation context persistence (`localStorage`), and test suites remain intact.

---

## 2. Stitch MCP Design Exploration & Translation

### 2.1 Stitch Project & Screen Generations
To explore and establish the enterprise visual direction before writing frontend code, the **Stitch MCP** server was utilized:
- **Project Created**: `projects/8879517819909373464` (*NexusRAG Modern Enterprise Light SaaS*)
- **Chat Assistant Screen**: `projects/8879517819909373464/screens/845e025148f7434ebac2ddb277efe6df`
- **Knowledge Base Screen**: `projects/8879517819909373464/screens/82cbf940566848d1bb33d442ec752043`
- **Management Modals Screen**: `projects/8879517819909373464/screens/93c6a34ccf80406fbedf6cebbf3bfb1d`

### 2.2 Translation to React Architecture
In accordance with architectural rules:
- No generated raw HTML/Tailwind bundles were dumped directly into the React tree.
- The Stitch design system tokens (hex codes, typography scales, border radii, card padding, and subtle shadows) were translated directly into `frontend/src/styles/index.css` via CSS variables.
- Component semantics, hooks, state machines, and Vitest test IDs were preserved 100%.

---

## 3. Design System & Design Tokens

The application transitioned from a dark `#080c14` background to a crisp `#F7F8FC` enterprise light theme with structured depth:

```css
:root {
  /* Surfaces & Backgrounds */
  --bg-base: #F7F8FC;        /* SaaS canvas background */
  --bg-surface: #FFFFFF;     /* Card and modal panels */
  --bg-subtle: #F1F3F7;      /* Hover states & pills */
  --bg-card: #FFFFFF;
  --bg-card-hover: #F8FAFD;
  --bg-elevated: #FFFFFF;
  --bg-input: #FFFFFF;

  /* Primary Brand — Enterprise Indigo */
  --primary: #4F46E5;
  --primary-hover: #4338CA;
  --primary-soft: #EEF2FF;
  --primary-border: #C7D2FE;
  --primary-subtle: #EEF2FF;

  /* Accent — Modern Violet */
  --accent: #7C3AED;
  --accent-soft: #F5F3FF;
  --accent-border: #DDD6FE;

  /* Typography Hierarchy */
  --text-primary: #111827;   /* High-contrast headings & query text */
  --text-secondary: #475569; /* Body text & document metadata */
  --text-muted: #94A3B8;     /* Timestamps, hints, placeholders */
  --text-highlight: #4F46E5;

  /* Borders & Dividers */
  --border: #E2E8F0;
  --border-strong: #CBD5E1;
  --border-subtle: #F1F5F9;
  --border-focus: #4F46E5;

  /* Status Colors */
  --success: #10B981;
  --success-soft: #ECFDF5;
  --success-border: #A7F3D0;
  --danger: #EF4444;
  --danger-hover: #DC2626;
  --danger-soft: #FEF2F2;
  --danger-border: #FECACA;
  --warning: #F59E0B;
  --warning-soft: #FFFBEB;
  --warning-border: #FDE68A;

  /* Consistent Radii */
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;          /* Buttons & inputs */
  --radius-lg: 12px;         /* Content cards & chat composer */
  --radius-xl: 16px;         /* Modals & dialogs */
  --radius-full: 9999px;     /* Badges & avatar pills */

  /* Subtle Modern Shadows */
  --shadow-xs: 0 1px 2px rgba(16, 24, 40, 0.04);
  --shadow-sm: 0 1px 3px rgba(16, 24, 40, 0.06), 0 1px 2px rgba(16, 24, 40, 0.04);
  --shadow-md: 0 4px 8px -2px rgba(16, 24, 40, 0.08), 0 2px 4px -2px rgba(16, 24, 40, 0.04);
  --shadow-modal: 0 24px 48px -12px rgba(16, 24, 40, 0.16), 0 0 0 1px rgba(16, 24, 40, 0.06);
}
```

---

## 4. Component Redesigns & Bug Fixes

### 4.1 Navbar Redesign
- **Structure**: Brand logo with lightning badge (`⚡ NexusRAG`), `Assistant` tag, navigation links (`Chat`, `Documents`), primary `+ New Chat` button, and backend connection pill (`Connected` with glowing green status dot).
- **Styling**: Sticky surface with subtle backdrop blur (`rgba(255, 255, 255, 0.92)` + `backdrop-filter: blur(12px)`), clean `#E2E8F0` border, and responsive behavior collapsing labels gracefully on small screens.

### 4.2 Chat Page & Integrated Composer Fix
- **Previous Layout Bug**: In earlier versions, the `<textarea>` and `Send` button were placed in disconnected containers or unstyled wrapper divs, causing the button to detach, misalign, and leak browser-native textarea borders.
- **Fixed Integrated Architecture**:
  - The chat input was redesigned into an integrated card container (`.chat-composer-card`) with a 12px radius, subtle border, and card shadow.
  - Inside the card, the textarea expands dynamically without borders or focus outlines (`border: none; outline: none; background: transparent; min-height: 48px; max-height: 180px`).
  - The card footer houses keyboard shortcut hints (`Shift+Enter for newline`), tabular character counter (`0/2000`), and an integrated purple `Send` button with an upward arrow SVG and accessible label.
  - The composer card stays attached cleanly to the bottom of the viewport using sticky positioning.

### 4.3 Chat Messages & Citations
- **User Bubble**: Right-aligned, styled with a soft indigo tint (`background: #EEF2FF; border: 1px solid #C7D2FE; color: #111827`).
- **Assistant Bubble**: Left-aligned, pure white surface (`background: #FFFFFF; border: 1px solid #E2E8F0; box-shadow: var(--shadow-sm)`).
- **Source Citations**: Compact source badges formatted with format tags (`.badge-pdf`, `.badge-md`, `.badge-txt`), page indicators, and text ellipsis with full filename in `title`.

### 4.4 Documents Table Overlap Bug Fix
- **Previous Layout Bug**: In the prior implementation, long filenames broke table bounds, overlapping the chunk count badge and the Replace/Delete action buttons.
- **Fixed Fixed-Table Architecture**:
  - Configured `.documents-table` with `table-layout: fixed; width: 100%; min-width: 620px;` inside a horizontal scroll container (`.table-container`).
  - Added a dedicated `Type` column separating the file extension badge from the filename.
  - Explicit column widths:
    - `Document` (`th.th-name`): `auto` (flexible remaining space, min 180px)
    - `Type` (`th.th-type`): `80px`
    - `Chunks` (`th.th-chunks`): `105px`
    - `Indexed` (`th.th-date`): `125px`
    - `Actions` (`th.th-actions`): `180px`
  - Long filenames truncate cleanly with single-line CSS ellipsis (`overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`) while retaining the full name in the `title` attribute for tooltips.
  - The action buttons (`[ Replace ]` and `[ Delete ]`) are grouped in a flex container (`.action-btn-group`) with `flex-wrap: nowrap`, ensuring buttons never overlap each other or adjacent cells.

---

## 5. Document Management CRUD Architecture

### 5.1 Backend REST API
Three new CRUD endpoints were integrated into `backend/app/api/routes_documents.py`:
1. **`GET /api/v1/documents`**:
   - Queries ChromaDB collection metadata to group documents by source.
   - Returns list of document records (`source`, `file_type`, `chunk_count`, `indexed_at`) along with total indexed chunk count.
2. **`DELETE /api/v1/documents/{source}`**:
   - Deletes all chunks associated with `source` from ChromaDB via `where={"source": source}`.
   - Clears the Redis query cache via `cache.clear()` to prevent stale RAG responses.
   - Returns 404 if source is not found.
3. **`PUT /api/v1/documents/{source}`**:
   - Atomic replacement: deletes existing chunks for `{source}`.
   - Validates, stages, and ingests the replacement file via `IngestionPipeline`.
   - Invalidates the Redis query cache.

### 5.2 Frontend Modals & State Machine
- **Delete Confirmation Modal** (`DeleteConfirmModal.jsx`):
  - Accessible dialog (`role="dialog"`, `aria-modal="true"`).
  - Listens for `Escape` key and backdrop clicks.
  - Displays destructive warning badge and explains embedding deletion.
- **Replace Document Modal** (`ReplaceDocumentModal.jsx`):
  - Drag-and-drop replacement zone.
  - Client-side format validation (`.pdf`, `.txt`, `.md`).
  - Displays replacement file name and size before committing.
  - Shows indeterminate loading progress bar during re-indexing.

---

## 6. Verification & Automated Test Results

### 6.1 Automated Test Execution

#### Backend Tests (Pytest)
```bash
& "D:\Academic-Projects\RAG\.venv\Scripts\python.exe" -m pytest tests/
```
**Result**: **168 passed**, 4 warnings in 9.09s.
- `tests/test_documents_crud.py`: 10/10 passed (list, delete, replace, cache invalidation, not found handling).
- All 158 prior tests across RAG pipeline, embeddings, vector store, chunking, and Redis cache passed with 0 failures.

#### Frontend Tests (Vitest)
```bash
npm test -- --run
```
**Result**: **52 passed** across 5 test suites in 3.11s.
- `src/__tests__/documents_crud.test.jsx`: 12/12 passed.
- `src/__tests__/conversations.test.jsx`: 19/19 passed.
- `src/__tests__/chat.test.jsx`: 11/11 passed.
- `src/__tests__/upload.test.jsx`: 6/6 passed.
- `src/__tests__/routing.test.jsx`: 4/4 passed.

#### Production Build (Vite)
```bash
npm run build
```
**Result**: Built cleanly in 3.04s.
- Bundle output: `dist/index.html` (0.81 kB), `dist/assets/index-fj35zyid.css` (26.40 kB), `dist/assets/index-Cyc9XpWJ.js` (435.88 kB).

### 6.2 Manual Browser Verification
End-to-end verification was performed in a live Chromium browser instance via the browser subagent:
1. **Chat Page (`/chat`)**:
   - Verified light theme rendering with clean white background and cards.
   - Tested typing into integrated composer; verified real-time character counter update (`76/2000`) and purple Send button activation.
   - Tested `+ New Chat` button; verified clean conversation reset.
2. **Documents Page (`/documents`)**:
   - Verified 2-column layout (68% document list, 32% upload panel).
   - Checked document table: confirmed Document, Type, Chunks, Indexed, and Actions columns align with zero overlapping. Long filenames truncate with ellipsis.
   - Tested Replace modal: verified dialog backdrop blur, dropzone, and Cancel button dismissal.
   - Tested Delete modal: verified warning dialog styling, impact warning, and Cancel button dismissal.
3. **Mobile Responsiveness (390px x 844px)**:
   - Verified navbar collapses gracefully.
   - Verified chat composer maintains touch-friendly proportions without overflow.
   - Verified document table container enables horizontal scroll without distortion.

---

## 7. Files Created & Modified

### Backend
- `backend/app/vectordb/chroma_store.py` (Modified): Added `list_sources()`, `count_by_source()`, `delete_by_source()`.
- `backend/app/cache/redis_cache.py` (Modified): Added `clear()` method to `BaseQueryCache` and `RedisQueryCache`.
- `backend/app/api/routes_documents.py` (Modified): Added `GET /documents`, `DELETE /documents/{source}`, and `PUT /documents/{source}` routes with staging cleanup.
- `backend/tests/test_documents_crud.py` (Created): 10 comprehensive unit/integration tests for document CRUD endpoints.

### Frontend
- `frontend/src/styles/index.css` (Modified): Complete conversion to light modern SaaS design system with CSS variables, table fixed layout, and integrated composer.
- `frontend/src/components/ChatInput.jsx` (Modified): Integrated composer card architecture with character counter and keyboard shortcut hint.
- `frontend/src/components/DocumentList.jsx` (Modified): Added dedicated `Type` column to table header and loading skeleton.
- `frontend/src/components/DocumentRow.jsx` (Modified): Clean separation of filename and type badge; non-overlapping action buttons.
- `frontend/src/components/DeleteConfirmModal.jsx` (Created): Accessible confirmation dialog for document deletion.
- `frontend/src/components/ReplaceDocumentModal.jsx` (Created): Modal dialog for document replacement and re-indexing.
- `frontend/src/components/EmptyDocumentState.jsx` (Created): Polished empty state with search reset capability.
- `frontend/src/hooks/useDocuments.js` (Created): React hook managing document CRUD operations and notifications.
- `frontend/src/services/api.js` (Modified): Added `listDocuments()`, `deleteDocument()`, and `replaceDocument()` API functions.
- `frontend/src/__tests__/documents_crud.test.jsx` (Created): 12 Vitest tests for document CRUD state and operations.

---

## 8. Technical Interview Questions & Answers

### Q1: Why use `table-layout: fixed` to solve table cell overlapping instead of `display: flex` or standard HTML table layout?
**Answer**: By default, HTML tables use `table-layout: auto`, where column widths are determined by the widest unbroken text content across all rows. When a cell contains a long string without spaces (e.g. `dsa_system_design_interview_preparation_handbook_v2.pdf`), the browser expands that cell beyond the viewport or compresses neighboring cells to their absolute minimum, causing button text to wrap, overlap, or clip. 

With `table-layout: fixed`, the browser calculates column widths strictly based on the table's width and explicit column declarations (e.g. `th.th-type { width: 80px }`, `th.th-actions { width: 180px }`). Flexible cells (`th.th-name { width: auto }`) are allocated the exact remaining width. Any child element inside a fixed table cell with `min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;` will truncate predictably with an ellipsis rather than blowing out the layout.

### Q2: Why is cache invalidation essential when deleting or replacing documents in a RAG system?
**Answer**: NexusRAG utilizes a Redis query cache that stores previous question-to-answer mappings hashed by normalized query text. If an indexed policy document is updated or deleted, cached responses to previous questions (e.g. "What is our leave policy?") would continue to be served from Redis if the cache is not invalidated, delivering outdated or revoked information. 

By executing `cache.clear()` upon `DELETE` or `PUT` of a document source, all cached query answers are purged, forcing subsequent queries to execute similarity search against the current ChromaDB vector store.

### Q3: How does client-side state management ensure chat persistence across navigation and page refreshes?
**Answer**: NexusRAG uses `ConversationContext` backed by browser `localStorage`. Each conversation is assigned an ID, title, and timestamp. The active conversation ID and list of conversations are synchronized to `localStorage` on every change. When navigating between `/chat` and `/documents`, React components mount and unmount, but `ConversationProvider` sits above the routing switch in the React DOM hierarchy, maintaining active message state in memory while guaranteeing durability across page refreshes via `localStorage`.

---

## 9. Conclusion

Phase 14 successfully elevates NexusRAG into a production-grade enterprise knowledge assistant. The combination of modern light visual aesthetics, robust table and composer layouts, and complete Document Management CRUD operations delivers a seamless, reliable user experience backed by 100% passing automated test coverage across both backend and frontend layers.
