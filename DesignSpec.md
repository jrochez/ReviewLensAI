# ReviewLens AI — UI Design Specification

**Version:** 1.0  
**Date:** 2026-05-27  
**Audience:** Internal ORM Analyst Team (MVP)  
**Aesthetic direction:** Clean internal tool — Notion meets Linear

---

## 1. Design Tokens

### 1.1 Color Palette

| Token | Hex | Usage |
|---|---|---|
| `color-accent` | `#2563EB` | Primary buttons, links, active states, badges |
| `color-accent-hover` | `#1D4ED8` | Hover state for accent elements |
| `color-accent-subtle` | `#EFF6FF` | Accent backgrounds (info banners, highlights) |
| `color-bg-base` | `#FFFFFF` | Page background |
| `color-bg-surface` | `#F9FAFB` | Card/panel backgrounds |
| `color-bg-raised` | `#F3F4F6` | Table row hover, input backgrounds |
| `color-border` | `#E5E7EB` | Dividers, card borders, input borders |
| `color-border-strong` | `#D1D5DB` | Focused input borders (unfocused) |
| `color-text-primary` | `#111827` | Headings, primary body copy |
| `color-text-secondary` | `#6B7280` | Labels, metadata, placeholder text |
| `color-text-disabled` | `#9CA3AF` | Disabled UI elements |
| `color-success` | `#16A34A` | "Ready" status badge, positive sentiment |
| `color-success-bg` | `#F0FDF4` | Success badge background |
| `color-warning` | `#D97706` | "Pending / Scraping" status badge |
| `color-warning-bg` | `#FFFBEB` | Warning badge background |
| `color-error` | `#DC2626` | "Error" status badge, error messages |
| `color-error-bg` | `#FEF2F2` | Error badge background |
| `color-neutral` | `#6B7280` | Neutral sentiment bar |
| `color-scope-guard-bg` | `#F3F4F6` | Off-topic AI response bubble background |
| `color-scope-guard-border`| `#D1D5DB` | Off-topic AI response bubble border |

**Accent rationale:** Blue `#2563EB` provides 4.63:1 contrast on white (passes WCAG AA for normal text). It is a familiar, trustworthy data-tool hue with no semantic overlap with the status colors.

### 1.2 Typography

**Typeface:** `Inter` (system fallback: `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`)  
Source: Google Fonts — single weight request keeps load minimal.

| Scale Token | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `text-display` | 24px | 600 | 1.3 | Page titles |
| `text-heading` | 18px | 600 | 1.4 | Card/section headings |
| `text-subheading` | 14px | 600 | 1.4 | Table column headers, labels |
| `text-body` | 14px | 400 | 1.6 | Body copy, table rows |
| `text-small` | 12px | 400 | 1.5 | Metadata, timestamps, badge text |
| `text-mono` | 13px | 400 | 1.5 | ASIN codes, technical strings — `JetBrains Mono` or `monospace` |

### 1.3 Spacing (8pt grid)

`4 | 8 | 12 | 16 | 24 | 32 | 48 | 64px`

### 1.4 Border Radius

| Token | Value | Usage |
|---|---|---|
| `radius-sm` | 4px | Badges, tags |
| `radius-md` | 8px | Cards, inputs, buttons |
| `radius-lg` | 12px | Modals, panels |
| `radius-full` | 9999px | Avatars, pill badges |

---

## 2. Navigation Structure / Information Architecture

```
/login                          — Public. Redirect to /datasets if authenticated.
/datasets                       — Protected. Main dashboard. Default landing.
/datasets/new                   — Protected. New dataset form + scraping progress.
/datasets/:id                   — Protected. Ingestion summary + stats.
/datasets/:id/chat              — Protected. Q&A interface.
```

**Global nav pattern:** Top header bar (persistent on all authenticated screens). No sidebar on data pages — sidebar only appears inside the chat interface.

**Auth guard:** Unauthenticated requests redirect to `/login` with a `?next=` param so the user lands back after logging in.

---

## 3. Screen Wireframes (ASCII)

### 3.1 Login Page — `/login`

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                                                             │
│              ┌───────────────────────────┐                  │
│              │                           │                  │
│              │   ◈  ReviewLens AI        │  ← Logo mark +  │
│              │                           │    product name  │
│              │   ─────────────────────   │    (accent color)│
│              │                           │                  │
│              │   Email                   │                  │
│              │   ┌─────────────────────┐ │                  │
│              │   │                     │ │                  │
│              │   └─────────────────────┘ │                  │
│              │                           │                  │
│              │   Password                │                  │
│              │   ┌─────────────────────┐ │                  │
│              │   │                     │ │                  │
│              │   └─────────────────────┘ │                  │
│              │                           │                  │
│              │   [error message area]    │                  │
│              │                           │                  │
│              │   ┌─────────────────────┐ │                  │
│              │   │     Sign In         │ │  ← Accent button │
│              │   └─────────────────────┘ │                  │
│              │                           │                  │
│              └───────────────────────────┘                  │
│                                                             │
│                    © ReviewLens AI  2026                    │
└─────────────────────────────────────────────────────────────┘
```

**Notes:**
- Card width: 400px, centered horizontally and vertically in viewport.
- Card background: `color-bg-surface`, border: `color-border`, `radius-lg`, subtle box-shadow (`0 1px 4px rgba(0,0,0,0.08)`).
- Logo mark: a simple lens/magnifier icon rendered in `color-accent`. SVG inline — no external dependency.
- Error message: red inline text (`color-error`) between password field and button. Appears only on failed auth.
- "Sign In" button: full width, `color-accent` background, white text.
- No "forgot password" or "sign up" link — internal tool, admin-provisioned accounts.

---

### 3.2 Datasets List — `/datasets`

```
┌─────────────────────────────────────────────────────────────┐
│  ◈ ReviewLens AI          [Search datasets...]   [JD ▾]    │
│  ──────────────────────────────────────────────────────────  │
│                                                             │
│  Datasets                              [+ New Dataset]      │
│                                                             │
│  ┌──────────────┬──────────┬──────────┬────────────┬──────┐ │
│  │ Product Name │ ASIN     │ Status   │ Updated    │      │ │
│  ├──────────────┼──────────┼──────────┼────────────┼──────┤ │
│  │ Wireless     │ B08N5... │ ● Ready  │ 2h ago     │ ··· │ │
│  │ Headphones X │          │          │            │      │ │
│  ├──────────────┼──────────┼──────────┼────────────┼──────┤ │
│  │ USB-C Hub    │ B09K2... │ ◌ Scrpng │ In progres │ ··· │ │
│  ├──────────────┼──────────┼──────────┼────────────┼──────┤ │
│  │ Standing Desk│ B07H5... │ ⚠ Error  │ 3 days ago │ ··· │ │
│  ├──────────────┼──────────┼──────────┼────────────┼──────┤ │
│  │ Webcam Pro   │ B0BK9... │ ◷ Pending│ 5 days ago │ ··· │ │
│  └──────────────┴──────────┴──────────┴────────────┴──────┘ │
│                                                             │
│  Showing 4 datasets                                         │
└─────────────────────────────────────────────────────────────┘

  "···" expands to a small popover menu:
  ┌──────────────┐
  │  View        │
  │  Re-scrape   │
  │  ─────────── │
  │  Delete      │  ← red text
  └──────────────┘
```

**Empty state (first-time user):**
```
┌─────────────────────────────────────────────────────────────┐
│  ◈ ReviewLens AI                                  [JD ▾]   │
│  ──────────────────────────────────────────────────────────  │
│                                                             │
│  Datasets                              [+ New Dataset]      │
│                                                             │
│            ┌────────────────────────────────┐               │
│            │                                │               │
│            │      [ inbox icon ]            │               │
│            │                                │               │
│            │   No datasets yet              │               │
│            │   Add your first Amazon        │               │
│            │   product to get started.      │               │
│            │                                │               │
│            │   [+ New Dataset]              │               │
│            │                                │               │
│            └────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

**Header breakdown:**
- Left: logo mark + product name (`text-heading`, accent color on mark)
- Center: search input (inline, 280px, `color-bg-raised`) — filters the table client-side
- Right: avatar circle (initials, `color-accent` bg) + caret triggering dropdown with "Sign out"

**Status badge design:**
| Status | Icon | Text color | Background |
|---|---|---|---|
| Ready | filled circle | `color-success` | `color-success-bg` |
| Scraping | animated spinner | `color-warning` | `color-warning-bg` |
| Pending | clock | `color-warning` | `color-warning-bg` |
| Error | triangle-exclamation | `color-error` | `color-error-bg` |

---

### 3.3 New Dataset + Scraping Progress — `/datasets/new`

**Step 1: Form**
```
┌─────────────────────────────────────────────────────────────┐
│  ◈ ReviewLens AI                                  [JD ▾]   │
│  ──────────────────────────────────────────────────────────  │
│                                                             │
│  ← Datasets    New Dataset                                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │  Product Name                                       │    │
│  │  ┌───────────────────────────────────────────────┐  │    │
│  │  │  e.g. Wireless Headphones X                   │  │    │
│  │  └───────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  Amazon URL or ASIN                                 │    │
│  │  ┌───────────────────────────────────────────────┐  │    │
│  │  │  e.g. B08N5WRWNW or https://amazon.com/dp/... │  │    │
│  │  └───────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  [validation error if shown]                        │    │
│  │                                                     │    │
│  │  [Start Scraping]        [Cancel]                   │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Step 2: Scraping in Progress (same URL, form replaced)**
```
┌─────────────────────────────────────────────────────────────┐
│  ◈ ReviewLens AI                                  [JD ▾]   │
│  ──────────────────────────────────────────────────────────  │
│                                                             │
│  ← Datasets    Scraping: Wireless Headphones X              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │  ● Fetching product metadata          ✓ Done        │    │
│  │  ● Collecting reviews (Bright Data)   ◌ In progress │    │
│  │  ○ Processing & embedding             —             │    │
│  │  ○ Indexing to knowledge base         —             │    │
│  │                                                     │    │
│  │  ████████████░░░░░░░░░░░░  48%  ~2 min remaining   │    │
│  │                                                     │    │
│  │  Last update: 847 reviews collected                 │    │
│  │                                                     │    │
│  │  This page will refresh automatically when done.    │    │
│  │  You can also [go back to Datasets] and return.     │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Notes:**
- Step indicator uses three states: pending (empty circle), in-progress (animated spinner), done (checkmark).
- Progress bar fill: `color-accent`. Track: `color-bg-raised`.
- Polling interval: 3 seconds. Status text updates in-place (no full page reload).
- On completion: auto-redirect to `/datasets/:id` (ingestion summary) with a success toast.
- On error: step turns red with error icon and a short message. Shows "Retry" button.

---

### 3.4 Dataset Detail / Ingestion Summary — `/datasets/:id`

```
┌─────────────────────────────────────────────────────────────┐
│  ◈ ReviewLens AI                                  [JD ▾]   │
│  ──────────────────────────────────────────────────────────  │
│                                                             │
│  ← Datasets    Wireless Headphones X  [ASIN: B08N5WRWNW]   │
│               ● Ready · Last scraped 2h ago                 │
│               [Re-scrape]                 [Ask Questions →] │
│                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐   │
│  │  Review Stats           │  │  Sentiment              │   │
│  │  ─────────────────────  │  │  ─────────────────────  │   │
│  │  2,341  total reviews   │  │  ████████████  68% Pos  │   │
│  │  ★★★★☆  4.2 avg rating  │  │  ████  18% Neutral      │   │
│  │  Jan 2022 – Apr 2026    │  │  ███  14% Negative      │   │
│  │  87% verified purchase  │  │                         │   │
│  └─────────────────────────┘  └─────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐   │
│  │  Top Themes             │  │  Reviews                │   │
│  │  ─────────────────────  │  │  ─────────────────────  │   │
│  │  [sound quality  847]   │  │  [Date ▾][Rating][Vrfd] │   │
│  │  [battery life   612]   │  │  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  │   │
│  │  [comfort        489]   │  │  ★★★★★ Apr 12 ✓        │   │
│  │  [noise cancel   401]   │  │  "Great sound, slight…" │   │
│  │  [microphone     289]   │  │  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  │   │
│  │  [connectivity   201]   │  │  ★★☆☆☆ Apr 10         │   │
│  │  [+ 14 more]            │  │  "Pairing is a pain…"   │   │
│  └─────────────────────────┘  └─────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  (review table expands full width below 2-col grid) │    │
│  │  Full Review Table — sortable, paginated            │    │
│  │  [Date ▾] [Rating] [Verified] [Review Text] [...]   │    │
│  │  Clicking a row expands to full review text inline  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Layout notes:**
- 2-col card grid uses CSS Grid: `grid-template-columns: 1fr 1fr`, 24px gap.
- At viewport < 1100px, collapses to single column.
- Review table is full width below the 4-card grid.
- "Ask Questions" button: `color-accent`, top-right of page subheader. Primary CTA.
- Star rating display: filled/half/empty SVG stars in `#F59E0B` (amber — distinct from status colors).
- Sentiment bars: horizontal stacked bars. Positive = `color-success`, Neutral = `color-neutral`, Negative = `color-error`. No pie chart — bars are faster to read at a glance.
- Theme tags: each tag = `[label  count]` in `color-bg-raised` pill, `color-text-primary` label, `color-text-secondary` count. Sorted by frequency descending.

**Review table:**
- Columns: Date | Rating (stars) | Verified (checkmark or dash) | Review (truncated to ~80 chars with ellipsis)
- Sort on Date and Rating columns — clicking header toggles asc/desc, shows chevron indicator.
- Row click expands an accordion below the row showing full review text + any metadata.
- Pagination: 25 rows/page. Simple Prev / [1 2 3 …] / Next controls.

---

### 3.5 Q&A Chat Interface — `/datasets/:id/chat`

```
┌─────────────────────────────────────────────────────────────┐
│  ◈ ReviewLens AI                                  [JD ▾]   │
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│  Datasets        │  Wireless Headphones X                   │
│  ─────────────── │  ─────────────────────────────────────── │
│                  │                                          │
│  ● Wireless      │  ┌──────────────────────────────────┐    │
│    Headphones X  │  │  Dataset: Wireless Headphones X  │    │
│    (active)      │  │  2,341 reviews · ● Ready         │    │
│                  │  └──────────────────────────────────┘    │
│  ○ USB-C Hub     │                                          │
│                  │       ┌────────────────────────────┐     │
│  ○ Webcam Pro    │       │ What are the main          │     │
│                  │       │ complaints about battery?  │     │
│  ○ Standing Desk │       └────────────────────────────┘     │
│                  │       USER                  Apr 12 14:32 │
│  ─────────────── │                                          │
│  ← All Datasets  │  ┌──────────────────────────────────┐   │
│                  │  │ AI  Answering about: Wireless     │   │
│                  │  │     Headphones X reviews          │   │
│                  │  │                                   │   │
│                  │  │ Based on 312 reviews mentioning   │   │
│                  │  │ battery, the top complaints are:  │   │
│                  │  │ 1. Life drops after 6 months      │   │
│                  │  │ 2. Case charging unreliable       │   │
│                  │  │ 3. No charge indicator light      │   │
│                  │  └──────────────────────────────────┘   │
│                  │  Apr 12 14:32                            │
│                  │                                          │
│                  │  ┌──────────────────────────────────┐   │
│                  │  │ AI  [scope guard]                 │   │
│                  │  │                                   │   │
│                  │  │ I can only answer questions       │   │
│                  │  │ about reviews for this product.   │   │
│                  │  │ Please ask something related to   │   │
│                  │  │ the review data.                  │   │
│                  │  └──────────────────────────────────┘   │
│                  │                                          │
│                  │  ┌──────────────────────────────────┐   │
│                  │  │  Ask a question about these    ↑ │   │
│                  │  │  reviews…                        │   │
│                  │  └──────────────────────────────────┘   │
└──────────────────┴──────────────────────────────────────────┘
```

**Layout notes:**
- Sidebar width: 220px, fixed, `color-bg-surface` background, `color-border` right border.
- Chat panel: flex column, messages scroll, input pinned to bottom.
- Sidebar dataset list: each item = product name (truncated) with status dot. Active item has `color-accent-subtle` background and `color-accent` left border (3px).
- "← All Datasets" link at sidebar bottom returns to `/datasets`.

**Chat bubble specs:**

| Bubble type | Alignment | Background | Border |
|---|---|---|---|
| User message | Right | `color-accent` | none |
| AI response | Left | `color-bg-surface` | `color-border` |
| Scope guard | Left | `color-scope-guard-bg` | `color-scope-guard-border` |

- User bubbles: white text on accent bg.
- AI bubbles: `color-text-primary` text, subtle shadow.
- Scope guard: `color-text-secondary` text, dashed border, no AI label — just the muted warning style. Optionally prefix with a small warning icon.
- Context label ("Answering about: …") inside AI bubble: `text-small`, `color-text-secondary`, displayed as a single line above the response body.
- Input box: full width minus padding, `radius-md` border, `color-border`. Send button right-inset (icon button, accent color, activates on Enter or click). Disabled when input is empty.
- Max message width: 75% of chat panel width to maintain readable line length.

---

## 4. Component Inventory

### 4.1 Foundation / Layout
| Component | Description |
|---|---|
| `AppShell` | Top header bar + page content area. Rendered on all authenticated pages. |
| `PageHeader` | Page title + breadcrumb + page-level actions (e.g., "New Dataset", "Ask Questions"). |
| `TwoColGrid` | Responsive 2-column CSS grid with standard gap, collapses to 1-col. |

### 4.2 Navigation
| Component | Description |
|---|---|
| `TopNav` | Logo, search bar, user avatar dropdown. |
| `UserMenu` | Dropdown from avatar: shows name/email + "Sign out". |
| `ChatSidebar` | Scrollable dataset list panel in Q&A view. |
| `Breadcrumb` | "← Datasets" back-link pattern. |

### 4.3 Data Display
| Component | Description |
|---|---|
| `DataTable` | Sortable columns, row expand accordion, pagination controls. |
| `StatCard` | Titled card with primary stat + supporting metadata lines. |
| `SentimentBar` | Horizontal stacked bar for pos/neu/neg breakdown with legend. |
| `ThemeTagList` | Ordered list of frequency-tagged keyword pills. |
| `StarRating` | Displays `n.n` rating as filled/half/empty stars. |
| `StatusBadge` | Pill badge for Pending / Scraping / Ready / Error with icon and color. |
| `ReviewRow` | Table row with expand-accordion for full review text. |

### 4.4 Forms & Inputs
| Component | Description |
|---|---|
| `TextInput` | Label + input + inline error message. Standard and monospace variants. |
| `PrimaryButton` | Full-width and inline variants. Accent fill. Loading spinner state. |
| `GhostButton` | Outlined/text style for secondary actions (Cancel, Re-scrape). |
| `DangerButton` | Red text variant for destructive actions (Delete). Used inside menus only. |
| `IconButton` | Square button containing only an icon (send button in chat). |

### 4.5 Feedback & Status
| Component | Description |
|---|---|
| `ProgressBar` | Determinate bar with percentage label and status text below. |
| `StepIndicator` | Vertical step list with pending / active / done / error states. |
| `Toast` | Top-right temporary notification. Success and error variants. Auto-dismisses at 4s. |
| `EmptyState` | Centered icon + heading + body copy + optional CTA button. |
| `InlineError` | Red text with warning icon, for form validation. |

### 4.6 Overlays
| Component | Description |
|---|---|
| `ActionMenu` | Small popover from "···" trigger. View / Re-scrape / Delete items. |
| `ConfirmDialog` | Modal for destructive confirm (delete dataset). Title + body + Cancel/Confirm. |

### 4.7 Chat-Specific
| Component | Description |
|---|---|
| `ChatBubble` | User, AI response, and scope-guard variants. |
| `ContextLabel` | Small metadata line at top of AI bubble ("Answering about: …"). |
| `ChatInput` | Textarea + inline send button. Expands up to 4 lines then scrolls. |
| `DatasetListItem` | Sidebar row with status dot, truncated name, active/hover states. |

---

## 5. Interaction Notes

### 5.1 Loading States

**Page loads:**
- Datasets list: table renders with skeleton rows (3 animated shimmer rows) while data fetches. Avoids layout shift.
- Dataset detail: each of the 4 cards renders a skeleton independently — they can resolve at different times.
- Chat history: skeleton bubbles on initial load.

**Button loading:**
- "Sign In": button text changes to a spinner while auth request is in flight. Disabled during this state.
- "Start Scraping": same pattern. After submit, the form transitions to the step indicator view.
- "Send" in chat: icon replaces with spinner, input becomes read-only until response streams in.

**AI response streaming:**
- Render tokens as they arrive (streaming). Show a blinking cursor at the end of the AI bubble during generation.

### 5.2 Empty States

| Screen | Empty State Trigger | Message |
|---|---|---|
| Datasets list | No datasets exist | "No datasets yet. Add your first Amazon product to get started." + "New Dataset" CTA |
| Search (datasets) | No results for query | "No datasets match '[query]'. Clear the search or add a new dataset." |
| Top themes | Fewer than 3 themes extracted | "Not enough theme data — try a dataset with more reviews." |
| Chat history | First message not yet sent | Show a prompt suggestion row: 3 example questions as ghost chips the user can click to auto-fill the input. |

### 5.3 Error States

| Scenario | Treatment |
|---|---|
| Login failed | Inline error below password field: "Invalid email or password." Do not clear the email field. |
| Form validation (new dataset) | Inline error per field. URL/ASIN field validates format on blur. |
| Scraping failed | Step indicator shows red error step with short message. "Retry" button appears. Dataset status = Error badge. |
| Chat API error | AI bubble with error styling: "Something went wrong. Please try again." + a "Retry" link inside the bubble. |
| Network offline | Toast notification: "Connection lost. Reconnecting…" Banner persists until back online, then auto-dismisses. |
| Session expired | Silent redirect to `/login?next=[current-path]` with toast on the login page: "Your session expired. Please sign in again." |

### 5.4 Confirmation Flows

- **Delete dataset:** Clicking "Delete" in the action menu opens a `ConfirmDialog` modal. Body: "Deleting [Product Name] will permanently remove all reviews and chat history. This cannot be undone." Cancel (ghost) / Delete (danger button).
- **Re-scrape:** No confirmation dialog — action is non-destructive (overwrites data with fresh scrape). Show a toast on confirmation: "Scraping started for [Product Name]."

### 5.5 Accessibility Notes

- All interactive elements have visible focus rings: `2px solid color-accent`, `2px offset`.
- Color is never the sole indicator: status badges use both color and a text label; sentiment bars have percentage text labels; the scope guard bubble uses both muted color and distinct border style.
- ARIA roles: `role="status"` on scraping progress text, `role="alert"` on toast and inline errors, `aria-live="polite"` on chat message container.
- Keyboard navigation in chat: Enter to send, Shift+Enter for newline.
- Minimum touch target: 44×44px for all buttons and clickable rows (relevant if ever used on a tablet).
- Skip-to-content link as first focusable element on each page.

### 5.6 Micro-interactions

- Dataset row hover: `color-bg-raised` background transition (100ms ease).
- Action menu open: fade-in + translate-Y (4px → 0) over 120ms.
- Status badge for "Scraping": spinner icon rotates continuously (CSS animation, `prefers-reduced-motion` respected — falls back to static icon).
- Progress bar fill: smooth CSS transition matching poll interval (2.8s ease-in-out so it doesn't jump on each 3s poll).
- Toast enter: slide in from top-right (200ms). Exit: fade out (150ms).
- Chat bubble appear: fade-in (150ms). No slide — keeps it calm.

---

## 6. Responsive Behavior

This is a desktop-first internal tool. Defined breakpoints:

| Breakpoint | Width | Change |
|---|---|---|
| Desktop (default) | ≥ 1200px | 2-col grid on detail page, full table columns |
| Laptop | 900–1199px | 2-col grid collapses to 1-col on detail page |
| Tablet fallback | 768–899px | Chat sidebar collapses to a dropdown selector at top; table hides "Verified" column |

No mobile breakpoint defined for MVP.

---

*End of spec.*
