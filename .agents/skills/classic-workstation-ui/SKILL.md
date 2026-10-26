---
name: classic-workstation-ui
description: >-
  Design and construct web interfaces with a classic, high-density, minimalist engineering workstation aesthetic (inspired by early Unix, Bell Labs, W3C technical standards, and vintage professional workstations). Use this skill whenever building or refining developer tools, inference clients, monitoring dashboards, system consoles, or whenever the user requests a minimal, clean, classic, non-bubble, non-modern interface.
---

# Classic Workstation UI Skill

This skill provides complete guidelines, layout architecture, CSS design tokens, and interaction patterns for creating professional, high-density engineering workstations.

The aesthetic prioritizes **usability, information density, clarity, and rock-solid simplicity** over consumer trends (bubbly chat pills, glowing gradients, pastel cards, and bouncy spring animations).

---

## 1. Aesthetic Tenets: What to Do & What to Avoid

| Category | Strict Anti-Patterns (NEVER USE) | Workstation Standard (ALWAYS USE) |
| :--- | :--- | :--- |
| **Corners** | Rounded pills (`border-radius: 12px`, `9999px`) | Sharp, crisp corners (`border-radius: 0`) |
| **Palette** | Soft pastels, neon purples, gradient meshes | Archival parchment (`#F8F6ED`), stone (`#ECEBE5`), soot black (`#1A1816`) |
| **Rules & Borders** | Heavy drop shadows, blurred glassmorphism | Hairline rules (`1px solid var(--border-rule)` or `#8E8A7E`) |
| **Containers** | Floating rounded bubble cards | Continuous document transcript with dividing rules |
| **Buttons** | Browser-default 3D beveled buttons (`outset`) | Flat stone/parchment surfaces, hairline borders, dark inversion on hover |
| **Label Brackets** | Artificial decorative brackets (`[Send]`, `[USER]`) | Clean plain text labels (`Send`, `USER`) |
| **Dialogs** | Native browser popups (`window.prompt`, `window.alert`) | In-place inline editing directly within the component |
| **Toasts** | Bottom-right toasts that block prompt typing | Strategic top-right toasts (`top: 38px; right: 14px;`) with auto-dismiss |
| **Streaming UI** | Clunky debug bars with 3D buttons | Unified single-line header with inline `Abort` / `Evict` actions |

---

## 2. Color Palette & Typography

Use the standard archival monochrome design tokens:

```css
:root {
  --bg-top-bar: #ECEBE5;        /* Neutral stone grey header */
  --bg-parchment: #F8F6ED;      /* Warm archival parchment page canvas */
  --bg-transcript: #FAF8F1;     /* Pale clean ledger background */
  --bg-card: #FAF8F1;
  --bg-btn: #EDEBE4;            /* Flat stone button surface */
  --border-frame: #C2B9A5;      /* Subdued structural outer borders */
  --border-transcript: #8E8A7E; /* Dividing hairline rules */
  --border-rule: #777777;       /* Section break rules */
  --border-dark: #333333;       /* High-contrast element borders */
  --text-main: #1A1816;         /* Deep soot/carbon black for maximum legibility */
  --text-muted: #555555;        /* Secondary technical metadata */
  --font-mono: 'IBM Plex Mono', Menlo, Consolas, 'Courier New', Courier, monospace;
  --success: #73C991;           /* Muted natural sage green */
  --danger: #C62828;            /* Brick red */
  --warning: #E5C07B;           /* Muted amber */
}
```

Full stylesheet available in [design-tokens.css](./references/design-tokens.css).

---

## 3. Four-Zone Workstation Layout

### Zone 1: Fixed Top Command Strip (`height: 32px`)
- Fixed header at the top of the viewport.
- Left: Application title (`app-title`, bold, monospace).
- Right: Native-styled `<select>` dropdowns (`top-select-btn`) with hairline border and flat action buttons (`New Session`, `Models`, `Evict VRAM`, `Settings ⚙`).

### Zone 2: Session Ledger (Left Sidebar, `width: 260px`)
- Formatted as an archival ledger of timestamped records: `YYYY-MM-DD HH:MM | Title`.
- **In-Place Inline Renaming**:
  - Double-clicking or clicking the hover `Rename` button replaces the title with `<input class="session-inline-rename-input">` inside the row.
  - The date prefix remains intact (`2026-10-26 21:45 | `).
  - Blur must be debounced by 100ms to avoid premature double-click blur cancellation.
  - `Enter` commits the rename; `Escape` cancels.
- **Hover Actions**: Subtle `Rename` and `✕` buttons appear only when hovering over the row.
- **Right-Click Context Menu**: Custom minimal dropdown at cursor position (`Rename`, `Delete`) rather than an aggressive full-page confirm dialog.

### Zone 3: Document Transcript (Center Canvas)
- Messages are formatted like an engineering report or technical transcript, NOT chat bubbles.
- **Message Headers**:
  `USER 22:20:59 · 38 tokens ---------------------------------------`
  `ASSISTANT · qwen3.5:9b · 842 tokens · 48.2 tok/s · TTFT: 180ms --------------------`
  The hairline rule extends across the remaining container width using `.msg-header::after { content: ""; flex: 1; height: 1px; background: var(--border-rule); }`.
- **Live Stream Header**:
  - Live loading stages (`Loading Model (11.5s)...`, `Evaluating Prompt...`) appear directly on the assistant header line.
  - Minimal inline actions (`Abort` and `Evict`) sit right in the header during inference and disappear once generation finishes.
  - Inside the message body: only a quiet monospaced terminal cursor (`▌`) blinks while waiting.
- **Reasoning Scratchpad**:
  - Wrapped in `<details class="reasoning-box">` with an archival summary bar.
  - Header displays `▼ Reasoning Scratchpad` on the left, and live timer (`Thinking... 12.4s (840 tokens)`) plus a flat `Copy` button on the right.
  - Timer updating must be centralized in a single updater function to prevent text-length fighting and rapid flickering.
- **Composer Command Bar**:
  - Sleek 32px height row pinned to the bottom of the transcript.
  - Flat rectangular textarea, `Attach` button, and `Send` button (which transitions to `Abort` during inference).

### Zone 4: Real-Time Telemetry Bar (`height: 26px`)
- Pinned to the very bottom of the window frame.
- Displays continuous tabular telemetry separated by `|`:
  `STATUS: READY | HOST: 127.0.0.1:11434 | MODEL: qwen3.5:9b | CTX: 1,840 / 32,768 (5.6%) | SPEED: 48.2 t/s | TTFT: 180 ms | VRAM: 6.2G GPU (100%)`

HTML templates for all components are provided in [components.html](./references/components.html).

---

## 4. Critical Interaction Patterns

### 1. In-Place Inline Editing (Never Native Popups)
When users double-click an editable entity:
1. Replace the text node with an `<input>` styled with `border-radius: 0; border: 1px solid var(--border-dark);`.
2. Delay `input.focus()` and `input.select()` by 60–100ms to allow the mouseup gesture to finish.
3. Ignore `blur` events for the first 100ms.
4. On `Enter` or valid `blur`, persist changes and re-render.
5. On `Escape`, discard changes without prompt.

### 2. Strategic Top-Right Toasts
- Position fixed at `top: 38px; right: 14px;` with `pointer-events: none;` on the container and `pointer-events: auto;` on the toast.
- Keeps the composer textarea, Send button, and bottom telemetry strip completely unobstructed.
- Compact single-line pill (~26px height), sharp 0px corners, dark carbon surface (`#181614`).
- Auto-dismisses in 2.8s; pauses when the cursor hovers over the message.

### 3. Active State Reflection in Data Tables
Whenever an item in a library or table is currently active/selected:
1. Display a prominent `ACTIVE` badge (`.model-active-badge`, `#1A1816` background, off-white text, 9.5px mono).
2. Change the row action button from `Select` to a solid dark `Active` button (`disabled`, non-clickable).
3. Apply a subtle row background tint (`background: #F0EAE0;`).

### 4. Zero-Bloat Copy Feedback
Never inject SVG checkmarks or icons into copy buttons. Simply swap the button text:
`btn.innerText = 'Copied!'; setTimeout(() => { btn.innerText = 'Copy'; }, 1500);`

Detailed interaction scripts are provided in [interaction-patterns.md](./references/interaction-patterns.md).

---

## 5. Implementation Verification Checklist

When adopting this workstation UI in any project, verify each item:

- [ ] Zero `border-radius` larger than 0px on buttons, inputs, modals, and toasts.
- [ ] No artificial `[...]` bracket characters in button text, headers, or action bars.
- [ ] No browser-default 3D beveled buttons (`outset`/`inset`).
- [ ] No `window.prompt()`, `window.alert()`, or native modal dialogs for editing.
- [ ] Double-click on list items smoothly transforms into an in-place input without flickering.
- [ ] Live inference status and `Abort` controls live on the message header line, not in stacked debug bars.
- [ ] Toasts appear in the top-right corner below the header bar, never covering input fields.
- [ ] Telemetry strip is fixed at the bottom with real-time hardware and stream diagnostics.
- [ ] Copy buttons swap text cleanly to `Copied!` and revert after 1.5s.
