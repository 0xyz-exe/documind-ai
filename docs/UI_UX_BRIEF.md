# UI/UX Design Brief — DocuMind AI

## Design Principles

1. **Document-first:** Focus on documents, not generic chat
2. **Evidence-visible:** Citations prominent, sources accessible
3. **Processing-transparent:** Clear status, errors, progress
4. **Privacy-obvious:** Local/remote indicators visible
5. **Accessible:** WCAG AA, keyboard nav, semantic HTML

## Visual Identity

**Palette:**
- Primary: Blue-600 (trust, intelligence)
- Secondary: Green-600 (success, "grounded")
- Accent: Amber-500 (citations, highlights)
- Neutral: Slate-50 to Slate-900 (dark mode support)

**Typography:**
- Headers: Inter (clean, professional)
- Body: Inter
- Code/citations: JetBrains Mono

**Spacing:** 4px base unit (Tailwind defaults)

## Theme Support

- Light mode (default)
- Dark mode (system preference or toggle)
- High contrast (accessibility)

## Core Screens

### 1. Workspace Dashboard

**Layout:** Sidebar + main content

**Sidebar (left, 240px):**
- Logo + workspace name
- Navigation:
  - Documents (icon + count)
  - Collections
  - Q&A History
  - Settings
- Storage usage indicator (visual bar)
- Mode indicator: "🟢 Local Mode" / "🔵 Remote LLM: OpenAI"

**Main content:**
- Welcome message (first use)
- Quick stats cards:
  - Total documents (with status breakdown)
  - Recent questions (count, last 7d)
  - Processing queue (if any)
- Recent activity feed:
  - "Document X indexed" (timestamp)
  - "Asked: <question>" (timestamp)
  - "Upload failed: Y" (timestamp, error link)

**Empty state:** "Welcome! Upload your first document to get started" + upload CTA

### 2. Document Library

**Header:**
- Title: "Documents"
- Search bar (filters name, content)
- Upload button (primary, right-aligned)
- View toggle: Grid / List

**Filters (horizontal bar):**
- Status: All | Indexed | Processing | Failed
- Type: All | PDF | DOCX | TXT | MD
- Sort: Name | Date | Size

**List view (default):**

Table columns:
1. Name (with file icon)
2. Status badge (color-coded: green=indexed, blue=processing, red=failed, gray=uploaded)
3. Type (PDF, DOCX, etc.)
4. Size (MB)
5. Pages/sections (if extracted)
6. Uploaded (relative time: "2h ago")
7. Actions (kebab menu: View | Delete)

**Grid view:**
Card per document:
- Document thumbnail (first page preview if PDF, icon otherwise)
- Name (truncated, tooltip)
- Status badge (top-right corner)
- Metadata (size, pages)
- Click → document detail

**Empty state:** "No documents yet. Upload PDF, DOCX, TXT, or MD files to start."

**Processing indicator:** 
- Progress bar (if backend provides %)
- Or spinner + status text: "Extracting text..." / "Generating embeddings..."

### 3. Document Upload

**Modal dialog:**

**Drag-drop zone (large, centered):**
- "Drag files here or click to browse"
- Supported formats: PDF, DOCX, TXT, MD (icons shown)
- Max size: 50 MB per file

**After selection:**
- File list with name, size, remove button
- Upload button (primary, bottom-right)

**During upload:**
- Progress bar per file
- Cancel button
- Status: "Uploading 2 of 5..."

**After upload:**
- Success: "5 files uploaded. Processing started."
- Partial failure: "3 uploaded, 2 failed: [errors]"
- Close button

**Validation errors (inline):**
- "File too large (max 50 MB)"
- "Unsupported file type"
- "Empty file"

### 4. Document Detail

**Layout:** 2-column

**Left column (60%):**
- Document metadata card:
  - Name (editable?)
  - Status badge
  - Type, size, pages
  - Uploaded date
  - Chunks count (if indexed)
  - Hash (truncated, tooltip)
- Processing log (if status != indexed):
  - Timeline: uploaded → queued → processing → indexed/failed
  - Errors (if any, expandable)
- Actions:
  - Download original
  - Reprocess (if failed)
  - Delete (confirmation modal)

**Right column (40%):**
- Document preview:
  - PDF: Embedded viewer (pdf.js or native iframe)
  - Text: Scrollable text preview (first 1000 lines)
  - DOCX: Extracted text preview
  - Paginated if multi-page

### 5. Collections

**List view:**
- Collection card:
  - Name
  - Description (optional)
  - Document count (badge)
  - Created date
  - Actions: Edit | Delete

**Create/Edit modal:**
- Name (required)
- Description (optional, textarea)
- Document multi-select (searchable dropdown)
- Save / Cancel

**Empty state:** "Create a collection to group related documents."

### 6. Document Search

**Integrated in Document Library:**

**Search bar:**
- Placeholder: "Search documents..."
- Dropdown (right side): "Keyword" | "Semantic" (default keyword)
- Enter to search

**Results:**
- Same table/grid as library
- Highlight matching text in results
- If semantic: show similarity score (0-100, tooltip: "relevance")
- Empty results: "No matches found. Try different keywords or semantic search."

**Filters apply:** Status, type, sort

### 7. Q&A Workspace

**Layout:** 3-column responsive (collapses to 2-col on tablet, 1-col on mobile)

**Left sidebar (20%, collapsible):**
- Collection selector (dropdown, "All documents" default)
- Conversation history (list):
  - Last 10 conversations
  - Title: first question (truncated)
  - Timestamp
  - Click → load conversation
- "New conversation" button (top)

**Center (50%):**
- Chat interface:
  - Messages (scrollable):
    - User message (right-aligned, blue bubble)
    - Assistant message (left-aligned, white/gray bubble)
    - Citations inline: [1], [2] (clickable, orange badges)
    - Timestamp (subtle, below message)
  - Input box (bottom, sticky):
    - Textarea (auto-expand, max 5 lines)
    - Send button (icon, primary)
    - Character count (if limit)
  - Loading state: Spinner + "Retrieving documents..." / "Generating answer..."

**Right sidebar (30%):**
- "Sources" panel (sticky, scrolls independently):
  - Retrieved chunks (per answer):
    - [1] Document name (link to doc detail)
      - Page/section
      - Excerpt (200 chars, highlighted search terms)
      - Relevance score (visual bar + %)
      - Click → expand full chunk + jump to doc preview
  - Empty: "Ask a question to see sources."

**Answer with insufficient evidence:**
- Message: "I couldn't find enough relevant information in the documents to answer this question confidently."
- Suggestions: "Try rephrasing, or upload more documents on this topic."

**Demo mode indicator (top banner, dismissible):**
- "🟡 Demo Mode: Using rule-based responses. Configure an LLM for real answers."

### 8. Source Citation Detail

**Expanded chunk view (modal or slide-out panel):**

**Header:**
- Document name (link)
- Page/section reference
- Close button

**Content:**
- Full chunk text (300-500 tokens)
- Highlighted query terms
- Context (prev/next chunks, optional, expandable)

**Actions:**
- "Open document" (jumps to page)
- "Copy excerpt"

### 9. Retrieval Diagnostics (Settings → Advanced)

**Developer/debug view:**

**Per query:**
- Query text
- Collection(s) searched
- Retrieval method (keyword/semantic/hybrid)
- Retrieved chunks count (before rerank)
- Top-5 chunks:
  - Chunk ID
  - Document
  - Page
  - Score
  - Excerpt (first 100 chars)
- Reranker scores (if applicable)
- Latency breakdown:
  - Retrieval: Xms
  - Rerank: Xms
  - Generation: Xms
  - Total: Xms

**Empty:** "No queries yet."

### 10. Ingestion Error Details

**Accessible from Document Library (failed docs):**

**Modal:**
- Document name
- Upload timestamp
- Error type:
  - "Text extraction failed"
  - "Embedding generation failed"
  - "Invalid file format"
  - "File too large"
  - "OCR required (not configured)"
- Error message (technical, expandable)
- Stack trace (collapsible, monospace)
- Actions:
  - Retry (if transient)
  - Delete
  - Report issue (mailto or GitHub issue link)

### 11. Model & Embedding Configuration (Settings)

**Form (2-column on desktop):**

**Embedding Model:**
- Provider: Local (dropdown: sentence-transformers models)
  - all-MiniLM-L6-v2 (default, fast, 384-dim)
  - all-mpnet-base-v2 (better, slower, 768-dim)
- Device: CPU | CUDA (if available, auto-detected)
- Test button: "Embed sample text" → shows latency

**LLM Provider:**
- Mode:
  - Demo (rule-based, no API key)
  - Local (llama-cpp, requires model path)
  - Remote API (OpenAI-compatible)
- If Remote:
  - API URL (default: https://api.openai.com/v1)
  - API Key (password field, stored server-side)
  - Model name (text input: gpt-4, gpt-3.5-turbo, etc.)
  - Max tokens (slider, 500-4000, default 1000)
  - Temperature (slider, 0-1, default 0.1)
  - Test button: "Send test prompt" → shows response + latency

**Chunking:**
- Strategy: Fixed-size | Paragraph-aware (disabled in MVP)
- Chunk size (tokens): slider, 200-1000, default 500
- Overlap (tokens): slider, 0-200, default 50
- Warning: "Changing chunking requires re-indexing all documents."
- Apply button (confirmation: "Re-index X documents?")

**Retrieval:**
- Top-k: slider, 1-20, default 5
- Similarity threshold: slider, 0-1, default 0.5 (only return chunks above)
- Reranking: Enabled (checkbox, disabled in MVP)

**Save button (bottom):** Validates + saves config.

### 12. Evaluation Datasets & Results (Settings → Evaluation)

**Datasets tab:**

**List:**
- Dataset cards:
  - Name
  - Questions count
  - Last run (timestamp, link to results)
  - Actions: Run | Edit | Delete

**Create dataset:**
- Name (required)
- Questions (table):
  - Question text
  - Expected answer (optional, for reference)
  - Relevant doc IDs (multi-select)
  - Relevant chunk IDs (optional, for recall)
  - Add row / remove row
- Import JSON (upload .json)
- Save

**Results tab:**

**List of evaluation runs:**
- Run ID (timestamp)
- Dataset name
- Config snapshot (embedding model, LLM, chunk size)
- Metrics (summary):
  - Retrieval Recall@5: 72%
  - Citation Precision: 100%
  - Answer Faithfulness: 85%
- View details (link)

**Run detail:**
- Config used (JSON, expandable)
- Metrics (cards with explanations)
- Per-question results (table):
  - Question
  - Retrieved (chunks count)
  - Recall (if gold chunks provided)
  - Citations valid? (✓/✗)
  - Faithfulness score (0-100)
  - View (link to full retrieval + answer)

**Export:** Download CSV / JSON

### 13. Workspace Settings

**Tabs:**

**General:**
- Workspace name (editable)
- Storage location (read-only, with copy button)
- Storage usage (bar chart: documents, vectors, DB)
- Clear conversation history (confirmation)

**Members (P1, multi-user):**
- User list (email, role, actions)
- Invite (email input, role selector)

**Privacy:**
- Mode indicator: Local / Remote LLM
- Data retention:
  - Delete documents after X days (off by default)
  - Clear conversations after X days (off by default)
- Logs:
  - Enable query logging (checkbox)
  - Enable error telemetry (checkbox, disabled in MVP)

**Security:**
- API keys (masked, reset button)
- Allowed origins (CORS, for API access)

**Danger zone:**
- Delete all documents (requires "DELETE" confirmation)
- Delete workspace (requires "DELETE WORKSPACE" confirmation)

### 14. Usage & Performance Metrics (Settings → Metrics)

**Dashboard:**

**Charts (last 30 days):**
- Documents ingested (bar chart per day)
- Questions asked (line chart)
- Avg retrieval latency (line chart, ms)
- Avg generation latency (line chart, s)

**Top documents (table):**
- Name
- Times retrieved (count)
- Last accessed

**Failed ingestions (table):**
- Name
- Error type
- Timestamp

**No invented data:** If no usage, show "No activity yet" on charts.

### 15. Security & Privacy Settings

(Merged into Workspace Settings → Privacy & Security tabs above)

## Component States

**Loading:**
- Skeleton loaders (gray animated bars) for lists/cards
- Spinner + text for operations
- Progress bar for uploads/processing

**Empty:**
- Icon + message + CTA (when applicable)
- Examples: "Upload your first document" / "No questions yet"

**Error:**
- Red border on inputs
- Error message below (red text, icon)
- Toasts for non-blocking errors (top-right, auto-dismiss 5s)
- Error pages (404, 500) with home link

**Success:**
- Green checkmark icon
- Toast: "Document uploaded successfully"
- Auto-dismiss after 3s

**Offline:**
- Banner (top, yellow): "Connection lost. Some features unavailable."
- Disable remote LLM features
- Local search still works

## Responsive Breakpoints

- **Desktop:** 1280px+ (3-col layouts)
- **Tablet:** 768-1279px (2-col, collapsible sidebars)
- **Mobile:** <768px (1-col, bottom nav)

**Mobile Q&A:**
- Single column
- Sources panel → bottom sheet (swipe up)
- Conversation history → slide-out drawer

## Accessibility

**WCAG AA compliance:**
- Color contrast: 4.5:1 (text), 3:1 (UI components)
- Keyboard navigation: all interactive elements focusable (tab order)
- Focus indicators: 2px solid ring
- Screen reader: semantic HTML, ARIA labels, alt text
- Reduced motion: respect `prefers-reduced-motion`
- Form validation: clear error messages, aria-invalid

**Keyboard shortcuts (optional, document in settings):**
- `/` : Focus search
- `n` : New conversation
- `u` : Upload document
- `Esc` : Close modal

## Interaction Patterns

**Citations:**
- Inline: [1], [2] (orange badge, clickable)
- Hover → show doc name + page
- Click → expand full chunk in right panel
- Double-click → open document at page

**Document preview:**
- PDF: iframe or pdf.js (zoomable, navigable)
- Text: Syntax-highlighted if code, plain otherwise
- Search in preview (Ctrl+F passthrough)

**Drag-drop:**
- Upload area: highlight on dragover
- Collections: drag doc into collection (future)

**Toast notifications:**
- Position: top-right
- Stack vertically
- Max 3 visible (older auto-dismiss)
- Actions: Dismiss (×) or action button

## Design System (shadcn/ui components)

**Use:**
- Button (variants: default, outline, ghost, destructive)
- Input, Textarea
- Select, Dropdown
- Dialog (modal)
- Badge (status, citations)
- Card (documents, stats)
- Table (data lists)
- Tabs (settings)
- Toast (notifications)
- Skeleton (loading)
- Progress (upload, processing)
- Accordion (expandable sections)

**Customize:** Colors (primary, accent), border-radius (8px default)

## Dark Mode

- Switch: Settings → Appearance → Theme (Light | Dark | System)
- Palette:
  - Background: Slate-950
  - Surface: Slate-900
  - Text: Slate-50
  - Borders: Slate-800
  - Primary: Blue-500
  - Accent: Amber-400

**Ensure:** Contrast maintained, citations readable.

## No Fake Data

- Empty states when no data
- Grayed-out or hidden features when unavailable (OCR, reranking)
- "N/A" for metrics not yet computed
- No placeholder counts, scores, or timestamps

## Design Deliverables

1. Wireframes (Figma/Sketch): 15 screens above
2. Component library (shadcn/ui + custom)
3. Style guide (colors, typography, spacing)
4. Interaction specs (hover, click, keyboard)
5. Responsive layouts (breakpoints)
6. Accessibility checklist

---

**Status:** Approved for implementation.  
**Next:** Frontend scaffolding with Next.js + shadcn/ui.
