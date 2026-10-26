# Interaction Patterns for Classic Workstation UIs

This document provides tested JavaScript implementation patterns for the dynamic behaviors required by the classic workstation aesthetic.

---

## 1. In-Place Inline Renaming (Zero Popups)

### The Problem
Using `window.prompt()` creates an jarring native dialog box that violates the embedded document feel. However, naive inline replacement on `dblclick` suffers from premature blur: the mouseup of the double-click gesture triggers a `blur` event immediately, destroying the input before the user can type.

### The Solution: Debounced Blur Protection

```javascript
function inlineRenameSession(itemEl, sessionId, currentTitle, onSave) {
  if (itemEl.classList.contains('renaming')) return;
  itemEl.classList.add('renaming');

  const dateStr = itemEl.dataset.timestamp || '2026-10-26 21:45';
  itemEl.innerHTML = '';

  const prefix = document.createElement('span');
  prefix.className = 'session-date-prefix';
  prefix.textContent = `${dateStr} | `;
  itemEl.appendChild(prefix);

  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'session-inline-rename-input';
  input.value = currentTitle;
  input.spellcheck = false;
  itemEl.appendChild(input);

  let allowBlur = false;
  let committed = false;

  const commit = () => {
    if (committed) return;
    committed = true;
    const val = input.value.trim();
    if (val && val !== currentTitle) {
      onSave(val);
    } else {
      renderSessionList();
    }
  };

  const cancel = () => {
    if (committed) return;
    committed = true;
    renderSessionList();
  };

  input.addEventListener('keydown', (e) => {
    e.stopPropagation();
    if (e.key === 'Enter') {
      e.preventDefault();
      commit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancel();
    }
  });

  input.addEventListener('blur', () => {
    if (allowBlur) commit();
  });

  // Stop click bubbling so row click doesn't trigger item selection
  input.addEventListener('click', (e) => e.stopPropagation());
  input.addEventListener('dblclick', (e) => e.stopPropagation());
  input.addEventListener('mousedown', (e) => e.stopPropagation());
  input.addEventListener('mouseup', (e) => e.stopPropagation());

  // 100ms delay protects against the tail end of the double-click gesture
  setTimeout(() => {
    allowBlur = true;
    input.focus();
    input.select();
  }, 100);
}
```

---

## 2. Stable Live Reasoning & Stream Timers (Zero Flicker)

### The Problem
If a background stopwatch (`setInterval`) and a token stream chunk handler (`onChunk` / `renderDOM`) format the same timer label with different strings (e.g. `12.4s` vs `Thinking... 12.4s (840 tokens)`), the label character length oscillates at 30–60Hz, causing an annoying visual seizure.

### The Solution: Unified Single Formatter

```javascript
// Centralized formatter called by both the stopwatch and DOM renderers
function updateLiveThoughtTimer() {
  if (!thoughtTimerEl || !isInsideThink || !thoughtStartTime) return;
  const elapsed = ((performance.now() - thoughtStartTime) / 1000).toFixed(1);
  const tokenCount = estimateTokens(accumulatedThought).toLocaleString();
  thoughtTimerEl.innerText = `Thinking... ${elapsed}s (${tokenCount} tokens)`;
}

// Background tick (every 100ms)
const timerInterval = setInterval(() => {
  if (!isGenerating) return;
  updateLiveThoughtTimer();
}, 100);

// Stream chunk arrival
function onStreamChunk(chunk) {
  accumulatedThought += chunk;
  updateLiveThoughtTimer();
}

// When thinking finishes:
function finalizeThinking() {
  const duration = ((performance.now() - thoughtStartTime) / 1000).toFixed(1);
  const totalTokens = estimateTokens(accumulatedThought).toLocaleString();
  thoughtTimerEl.innerText = `Thought for ${duration}s (${totalTokens} tokens)`;
}
```

---

## 3. Strategic Top-Right Toasts

### Rules
1. Never place toasts at the bottom right where they obstruct prompt typing, Send buttons, or status telemetry.
2. Position fixed at `top: 38px; right: 14px;` with `pointer-events: none;` on container and `pointer-events: auto;` on toasts.
3. Keep single-row height (~26px), flat dark carbon surface (`#181614`), and 0px corners.

```javascript
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icon = type === 'success' ? '✓' :
               type === 'error'   ? '✕' :
               type === 'warning' ? '▲' : '·';

  // Prevent duplicate checkmarks
  const clean = String(message).replace(/^✓\s*/, '');

  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <span class="toast-msg">${escapeHtml(clean)}</span>
    <button type="button" class="toast-close" title="Dismiss">✕</button>
  `;

  let timer = null;
  const dismiss = () => {
    if (timer) clearTimeout(timer);
    toast.classList.remove('visible');
    setTimeout(() => toast.remove(), 160);
  };

  toast.querySelector('.toast-close').addEventListener('click', dismiss);

  // Pause auto-dismiss if user hovers to read long message
  toast.addEventListener('mouseenter', () => { if (timer) clearTimeout(timer); });
  toast.addEventListener('mouseleave', () => { timer = setTimeout(dismiss, 1200); });

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('visible'));
  timer = setTimeout(dismiss, 2800);
}
```

---

## 4. Minimal Right-Click Context Menu

```javascript
const ctxMenu = document.getElementById('sessionContextMenu');
let contextTargetId = null;
let contextTargetItem = null;

function openContextMenu(e, id, itemEl) {
  e.preventDefault();
  e.stopPropagation();
  contextTargetId = id;
  contextTargetItem = itemEl;

  ctxMenu.style.display = 'block';
  ctxMenu.style.left = `${Math.min(window.innerWidth - 120, e.clientX)}px`;
  ctxMenu.style.top = `${Math.min(window.innerHeight - 80, e.clientY)}px`;
}

document.addEventListener('click', () => {
  if (ctxMenu) ctxMenu.style.display = 'none';
});

document.getElementById('ctxMenuRename').addEventListener('click', (e) => {
  e.stopPropagation();
  ctxMenu.style.display = 'none';
  if (contextTargetId && contextTargetItem) {
    inlineRenameSession(contextTargetItem, contextTargetId);
  }
});
```

---

## 5. Clean Copy Feedback (No SVG Bloat)

```javascript
function copyWithFeedback(buttonEl, textToCopy, toastMsg = 'Copied to clipboard') {
  navigator.clipboard.writeText(textToCopy).then(() => {
    const orig = buttonEl.innerText;
    buttonEl.innerText = 'Copied!';
    setTimeout(() => {
      buttonEl.innerText = orig;
    }, 1500);
    if (toastMsg) showToast(toastMsg, 'success');
  });
}
```
