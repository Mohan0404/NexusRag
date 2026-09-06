# Phase 12 — React Frontend Layer

## 1. Objective

Build a modern, responsive, accessible React frontend for the Genworx Knowledge Assistant (`NexusRAG`).

The frontend interfaces directly with the Phase 11 FastAPI backend REST API (`GET /api/v1/health`, `POST /api/v1/chat`, and `POST /api/v1/documents/upload`), enabling users to:
1. Ask natural language questions against indexed enterprise documents.
2. View grounded assistant answers accompanied by source citations with page numbers.
3. Upload and index PDF, TXT, and Markdown documents into ChromaDB.
4. Monitor upload and indexing progress via clear indeterminate state indicators.
5. Experience reliable error messaging without exposing backend stack traces or server paths.
6. Seamlessly switch between Chat and Documents interfaces on desktop and mobile viewports.

---

## 2. Architecture

```text
                                  React Frontend
                             (Vite + React Router)
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 │                                           │
          /chat (ChatPage)                         /documents (DocumentsPage)
                 │                                           │
          useChat() Hook                             DocumentUploader
                 │                                           │
         api.sendChatMessage()                      api.uploadDocument()
      (POST /api/v1/chat JSON)                  (POST /api/v1/documents/upload FormData)
                 │                                           │
                 ▼                                           ▼
         FastAPI Backend                             FastAPI Backend
       (RAGPipeline.query())                     (IngestionPipeline.index_file())
                 │                                           │
        ┌────────┴────────┐                         ┌────────┴────────┐
   [Cache Hit]       [Cache Miss]               [ChromaDB]       [Redis Cache]
   (Redis Fast)    (ChromaDB + LLM)             (Indexed)          (Cleared)
                 │                                           │
                 ▼                                           ▼
       ChatResponse (JSON)                       DocumentUploadResponse (JSON)
                 │                                           │
                 ▼                                           ▼
       Render Answer & Sources                  Render Chunks Indexed & Stats
```

---

## 3. Frontend Structure

```text
frontend/
├── index.html                      # HTML entry point (Inter font, viewport meta)
├── package.json                    # Dependencies & scripts (React, Vite, Vitest)
├── vite.config.js                  # Vite & Vitest configuration
├── .env.example                    # Template documenting VITE_API_BASE_URL
├── .env                            # Local development environment (ignored by Git)
├── public/
│   └── favicon.ico
└── src/
    ├── main.jsx                    # Mounts App inside BrowserRouter
    ├── App.jsx                     # Top-level shell with Navbar and Routes
    ├── setupTests.js               # Vitest environment setup with jest-dom
    ├── components/
    │   ├── Navbar.jsx              # Navigation bar & mount-time health check badge
    │   ├── ChatWindow.jsx          # Scrollable message viewport & welcome state
    │   ├── ChatMessage.jsx         # User & assistant bubbles with citations
    │   ├── ChatInput.jsx           # Auto-resizing textarea with char counter
    │   ├── SourceCard.jsx          # Grounded citation pill (type, filename, page)
    │   ├── DocumentUploader.jsx    # File drag/drop, pre-validation & upload flow
    │   └── LoadingIndicator.jsx    # Pulsating dots during RAG generation
    ├── pages/
    │   ├── ChatPage.jsx            # Main Q&A conversation view
    │   └── DocumentsPage.jsx       # Knowledge base upload & management view
    ├── hooks/
    │   └── useChat.js              # Encapsulated state & actions for chat
    ├── services/
    │   └── api.js                  # HTTP client using native window.fetch()
    ├── utils/
    │   └── helpers.js              # Byte formatting, filename sanitization
    ├── styles/
    │   └── index.css               # Vanilla CSS design system
    └── __tests__/
        ├── chat.test.jsx           # Unit tests for Chat, Input, and Health (11 tests)
        └── upload.test.jsx         # Unit tests for Document Upload (6 tests)
```

---

## 4. Components

1. **`Navbar.jsx`**: Top navigation with brand identity ("⚡ NexusRAG Assistant"), active navigation links (`Chat`, `Documents`), and a live backend health badge (`Connected` / `Offline`) checked once when the component mounts.
2. **`ChatPage.jsx`**: Page container orchestrating `useChat()` hook state, passing messages and handlers to `ChatWindow` and `ChatInput`.
3. **`ChatWindow.jsx`**: Renders message bubbles, auto-scrolls to the bottom on new messages, and displays a friendly empty state with clickable prompt suggestion chips.
4. **`ChatMessage.jsx`**: Formats individual messages. Differentiates user (aligned right, primary blue) and assistant (aligned left, card background) bubbles, rendering source citations below the answer.
5. **`ChatInput.jsx`**: Multiline input with auto-expansion, 2,000-character counter badge, disabled submit during active requests, and keyboard controls (`Enter` to submit, `Shift+Enter` for newline).
6. **`SourceCard.jsx`**: Renders citation pill with file type badges (`.pdf` rose, `.txt` blue, `.md` emerald), sanitized filename, and `Page X` tag (gracefully omitted if page number is unavailable).
7. **`DocumentsPage.jsx`**: Knowledge base overview explaining supported formats and rendering `DocumentUploader`.
8. **`DocumentUploader.jsx`**: Drag-and-drop file upload zone, client-side validation, indeterminate progress bar during upload/indexing, and success statistics summary.
9. **`LoadingIndicator.jsx`**: Animated pulsating indicator displayed while the assistant is searching the vector store and generating an answer.

---

## 5. Routing

Client-side routing is handled by `react-router-dom`:
- `/chat`: Displays `<ChatPage />`.
- `/documents`: Displays `<DocumentsPage />`.
- `/`: Automatically redirects to `/chat` (`<Navigate to="/chat" replace />`).
- Unknown routes (`*`): Fallback redirect to `/chat`.

`<NavLink>` is used in `<Navbar />` to apply an `.active` style to the currently active tab.

---

## 6. API Client (`services/api.js`)

Centralized HTTP client using the browser's native `window.fetch()` API:
- Base URL sourced from `import.meta.env.VITE_API_BASE_URL` (fallback: `http://localhost:8000/api/v1`).
- Custom `ApiError` class capturing HTTP status code, backend details, and normalized user-facing messages.
- Supported methods:
  - `checkHealth()`: `GET /health` -> `{ status: "healthy" }`.
  - `sendChatMessage(question)`: `POST /chat` with JSON body `{ question }`.
  - `uploadDocument(file)`: `POST /documents/upload` using `FormData`.

---

## 7. Chat Flow

1. User enters a question in `ChatInput` (or clicks an empty-state suggestion chip).
2. Input is validated locally (non-empty, non-whitespace, `<= 2000` chars).
3. `useChat()` appends the user query to `messages` and sets `isLoading = true`.
4. `api.sendChatMessage(question)` sends `POST /api/v1/chat`.
5. `LoadingIndicator` displays: *"Searching knowledge base & generating answer..."*.
6. On success (`200 OK`):
   - Assistant message is appended with answer text, citations list, and model identifier.
7. On failure (`422`, `500`, `502`, or Network failure):
   - An error banner is displayed with a user-friendly message, and an error card is appended to the conversation flow.
8. `isLoading` is set to `false`, and `ChatInput` re-enables.

---

## 8. Document Upload Flow

Implemented using an approved 5-state machine (`idle`, `selected`, `uploading`, `success`, `error`):
1. **Idle**: Drop zone is visible with format badges (`.pdf`, `.txt`, `.md`) and 10 MB limit notice.
2. **Selected**: User selects or drops a file. Client validates extension, 0-byte check, and size limit. File details (name, size, format) and an "Upload & Index" button are displayed.
3. **Uploading (Indeterminate Progress)**:
   - User clicks "Upload & Index".
   - State shifts to `uploading`.
   - An animated, indeterminate gradient progress bar displays along with the message: *"Extracting text, computing dense embeddings, and updating ChromaDB persistent vector store"*.
   - **No fake numeric percentages are shown.**
4. **Success**:
   - Backend completes ingestion and returns `200 OK`.
   - Success card displays filename, formatted file size, and total chunks created.
   - Provides a "Go to Chat" button to immediately query the new document.
5. **Error**:
   - If validation or server error occurs, an error banner displays specific advice (e.g. *"File exceeds 10 MB limit"*), allowing the user to select another file.

---

## 9. `FormData` & Multipart Uploads

For binary document ingestion:
```javascript
const formData = new FormData();
formData.append('file', file);

await fetch(`${BASE_URL}/documents/upload`, {
  method: 'POST',
  body: formData, // Browser automatically sets Content-Type with boundary string
});
```
Manually setting `Content-Type: multipart/form-data` is deliberately avoided so the browser generates the required boundary parameter automatically.

---

## 10. Client vs Server-Side Validation

| Rule | Client-Side (UX Only) | Server-Side (Authoritative Boundary) |
|---|---|---|
| Question Length | Max 2000 chars (live counter) | Pydantic `min_length=1, max_length=2000` (`422`) |
| Empty / Whitespace Query | Disables Send button | `@field_validator` rejects whitespace (`422`) |
| Allowed File Formats | Checks `.pdf`, `.txt`, `.md` extension | Whitelist check against `Settings.allowed_extensions` (`400`) |
| Maximum File Size | Checks `file.size <= 10 * 1024 * 1024` | 64 KB streaming buffer limit enforcement (`413`) |
| Empty File (0 Bytes) | Checks `file.size === 0` | 0-byte stream check (`400`) |

---

## 11. State Management

No external state management libraries (Redux, Zustand) were introduced. All state is maintained with React built-ins:
- **`useChat` Hook**: Manages `messages`, `isLoading`, `error`, `sendMessage()`, and `clearChat()`.
- **`DocumentUploader` Local State**: Manages `file`, `uploadStatus`, `uploadResult`, and `errorMessage`.
- **`Navbar` Local State**: Manages `healthStatus` ('checking' | 'connected' | 'offline').

---

## 12. Error Handling

Backend HTTP errors are normalized into human-readable messages:
- **`400 Bad Request`**: *"Unsupported file type. Please upload PDF, TXT, or Markdown."*
- **`413 Payload Too Large`**: *"File is larger than the 10 MB limit."*
- **`422 Unprocessable Entity`**: *"Document could not be processed or contains no readable text."* (Upload) or *"Question must be between 1 and 2,000 characters."* (Chat).
- **`500 Internal Server Error`**: *"Document processing failed. Please try again."* / *"An internal server error occurred while processing your question."*
- **`502 Bad Gateway`**: *"The AI service is temporarily unavailable. Please try again shortly."*
- **Network Error**: *"Unable to connect to the NexusRAG backend."*

---

## 13. CORS Configuration

Backend `Settings.CORS_ORIGINS` explicitly includes:
- `http://localhost:5173` (Vite dev server default)
- `http://localhost:3000`

The browser allows cross-origin requests from the React frontend running on port 5173 to FastAPI running on port 8000.

---

## 14. Environment Configuration

- **`frontend/.env.example`** (tracked in Git):
  ```ini
  # NexusRAG Frontend Environment Configuration Template
  VITE_API_BASE_URL=http://localhost:8000/api/v1
  ```
- **`frontend/.env`** (ignored in `.gitignore`):
  ```ini
  VITE_API_BASE_URL=http://localhost:8000/api/v1
  ```
- **Security**: No API keys or secrets are stored in or accessible to the frontend.

---

## 15. Accessibility (a11y)

- **Semantic Landmarks**: `<header>`, `<nav>`, `<main>`, `<form>`, `<button>`.
- **Screen Reader Support**: Chat window uses `role="log"` and `aria-live="polite"`.
- **Keyboard Navigation**:
  - Full tab traversal with visible `:focus-visible` focus rings.
  - Chat input supports `Enter` to submit and `Shift+Enter` for newline.
  - Drop zone supports `Enter` / `Space` keyboard activation.
- **Labels**: Hidden accessible `<label>` for text areas and file inputs.

---

## 16. Testing Strategy

Automated unit tests are implemented using **Vitest**, **React Testing Library**, and **jsdom** with mocked `window.fetch`:
- **`src/__tests__/chat.test.jsx` (11 tests)**:
  1. Navbar renders brand and navigation links.
  2. Chat input renders textarea and submit button.
  3. Empty/whitespace input disables submit button.
  4. Typing updates character count (e.g. 25/2000) and enables submit.
  5. Pressing Enter triggers submission.
  6. Assistant response renders grounded answer.
  7. Source citations render filename, format badge, and page number.
  8. Loading indicator renders during pending request.
  9. Internal server error (500) renders user-friendly error banner.
  10. Upstream provider outage (502) renders specific provider message.
  18. Navbar shows Connected status when health check succeeds.
  19. Navbar shows Offline status when health check fails.
- **`src/__tests__/upload.test.jsx` (6 tests)**:
  11. DocumentUploader renders drop zone and format badges.
  12. Unsupported file extension (.exe) is rejected client-side.
  13. File exceeding 10 MB limit is rejected client-side.
  14. Zero-byte file is rejected client-side.
  15. Valid upload sends `FormData` with method `POST`.
  16. Success response displays chunk count and "Go to Chat" button.
  17. Server error (413) displays user-friendly error message.

Total: **17 tests, 17 passed (100%)**.

---

## 17. Build Verification

Production build completed using `vite build`:
```text
dist/index.html                   0.81 kB │ gzip:   0.45 kB
dist/assets/index-CTRe0C84.css   10.95 kB │ gzip:   2.82 kB
dist/assets/index-DAdOBfyG.js   391.74 kB │ gzip: 117.09 kB
✓ built in 2.52s
```
Zero build errors or unresolved imports.

---

## 18. Manual Integration Test

1. **Backend Verification**: FastAPI running on `http://localhost:8000`, `GET /api/v1/health` returned `{"status": "healthy"}`.
2. **Frontend Dev Server**: Vite started on `http://localhost:5173`.
3. **Browser Execution**: Verified via Chromium subagent:
   - Root URL redirected to `http://localhost:5173/chat`.
   - Navbar displayed "⚡ NexusRAG Assistant" with green "Connected" indicator.
   - Welcome message and all three prompt chips displayed cleanly.
   - Clicked "Documents" link -> navigated to `/documents` with drop zone.
   - Clicked "Chat" link -> navigated back to `/chat`.

---

## 19. Design Decisions

1. **Vanilla CSS over Frameworks**: Handcrafted CSS custom properties ensure zero framework bloat and maximum styling control without Tailwind or Bootstrap.
2. **Indeterminate Upload Progress**: Since standard `fetch()` does not expose upload progress events, an animated indeterminate bar accurately conveys work in progress without displaying invented percentages.
3. **Single-Mount Health Check**: Checks backend status once when the navbar mounts, avoiding repetitive network polling.
4. **No Premature State Libraries**: React's built-in `useState`, `useCallback`, and custom `useChat()` provide sufficient reactivity without Redux overhead.

---

## 20. Limitations

1. **In-Memory Chat State**: Conversation history resets when the browser tab is refreshed.
2. **No Streaming Responses**: Answers appear as complete blocks after generation finishes.
3. **Single File Upload**: Files must be uploaded individually rather than in bulk.
4. **Large File Ingestion Latency**: Ingestion of large documents takes longer because it performs parsing, chunking, embedding generation, and vector indexing.

---

## 21. Future Improvements

1. **Server-Sent Events (SSE)**: Stream tokens from OpenRouter/Gemini to the UI in real time.
2. **IndexedDB Session Persistence**: Cache conversation history locally in the browser.
3. **Multi-File Batch Upload**: Allow users to drag multiple files at once.
4. **Dark/Light Theme Toggle**: User-switchable color schemes.

---

## 22. Interview Questions & Answers

### Q1: Why use `FormData` instead of `application/json` for file uploads?
**A**: JSON cannot transmit binary data without encoding it to Base64, which adds ~33% bandwidth overhead and requires loading the entire file into JavaScript memory. `FormData` uses standard `multipart/form-data` encoding, allowing browsers to stream binary file data directly from disk to the HTTP connection.

### Q2: Why avoid setting `Content-Type: multipart/form-data` manually in `fetch()`?
**A**: When `FormData` is passed to `fetch()`, the browser automatically computes and sets the `Content-Type` header along with the unique MIME boundary delimiter (e.g. `boundary=----WebKitFormBoundary...`). If you set `Content-Type` manually, the boundary string is omitted, causing the backend multipart parser to fail.

### Q3: Why is an indeterminate progress bar preferred over a simulated percentage bar?
**A**: Native `fetch()` does not emit upload progress events, and the server-side ingestion involves indeterminate steps (parsing, external embedding API calls, vector DB writes) whose exact duration varies by document structure. Displaying simulated percentages creates misleading expectations. An indeterminate indicator honestly signals that processing is actively underway.

### Q4: What is the purpose of encapsulating chat logic into `useChat()`?
**A**: It separates business and network logic from presentation components. `useChat()` handles asynchronous state transitions, error catching, and message formatting. `ChatPage`, `ChatWindow`, and `ChatInput` remain purely presentational, making them simpler to read, maintain, and unit test.

### Q5: How does CORS function between Vite on port 5173 and FastAPI on port 8000?
**A**: Because port 5173 and port 8000 have different origins, the browser blocks cross-origin requests by default. Before sending non-simple requests or when reading responses, the browser checks CORS headers. FastAPI's `CORSMiddleware` includes `http://localhost:5173` in `allow_origins`, returning `Access-Control-Allow-Origin: http://localhost:5173` and enabling communication.
