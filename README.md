# Ollama Studio

A minimalist local inference workstation and client interface for [Ollama](https://ollama.com).

Ollama Studio is designed with an emphasis on usability, information density, and a classic engineering document aesthetic. It runs entirely in the browser as a standalone single-page application with zero build tools, package managers, or external runtimes—requiring only a standard static web server (such as Python's built-in `http.server`) to serve client assets.

---

## Architecture & How It Works

Ollama Studio operates strictly on the client side, communicating directly with the local Ollama daemon via its REST endpoints.

```
┌──────────────────────────────────────┐          REST / Streams          ┌──────────────────────────┐
│          Ollama Studio UI            │ ───────────────────────────────> │      Ollama Daemon       │
│  (index.html · HTML5 / CSS3 / ES6)   │ <─────────────────────────────── │  (http://127.0.0.1:11434) │
└──────────────────────────────────────┘   /api/chat, /api/ps, /api/show  └──────────────────────────┘
                   │
                   ▼
         Browser localStorage
     (sessions, settings, cache)
```

- **Client-Side Storage**: Conversations, model configurations, and UI settings persist exclusively in browser `localStorage`. No telemetry, analytics, or user inputs ever leave the local machine.
- **Direct Daemon Integration**:
  - `/api/tags`: Discovers locally pulled models and displays metadata.
  - `/api/ps`: Monitors active memory residency and GPU VRAM offload percentages in real time.
  - `/api/show`: Inspects model architecture, parameter size, context capacity, and quantization format.
  - `/api/chat`: Streams responses using native `ReadableStream` chunks with live token evaluation.
  - `/api/generate`: Issues instant memory eviction requests (`keep_alive: 0`) to release GPU memory on demand.
  - `/api/pull`: Downloads models with real-time progress and bandwidth indicators.

---

## Core Capabilities

### Technical Engineering Layout
- **High-Density Document Canvas**: Structured like a technical ledger rather than a bubbly consumer chat app. Clean hairline rules, sharp 0px corners, and an archival parchment aesthetic.
- **Session Ledger**: Left sidebar organizes conversations with timestamps (`YYYY-MM-DD HH:MM`). Supports inline in-place renaming (double-click or hover action), search filtering, and a right-click context menu.
- **Top-Right Status Toasts**: Compact, single-row notifications positioned out of the way of the composer and telemetry bars, with auto-dismiss and hover-pause.

### Telemetry & Memory Monitoring
- **Live Stream Metrics**: Header and status strip display Time to First Token (TTFT), real-time generation speed (tokens per second), prompt evaluation duration, and total turnaround time.
- **VRAM Residency & Instant Eviction**: Detects whether model weights are 100% loaded in GPU VRAM or partially offloaded to system RAM. Includes a one-click "Evict VRAM" control to clear GPU memory without restarting the Ollama service.
- **Unified Header Stream Control**: Real-time loading stages (`Loading Model...`, `Evaluating Prompt...`) and inline `Abort` / `Evict` actions are integrated directly into the assistant header line during generation.

### Context Window & Model Controls
- **Expanded Context Presets**: Configurable context size (`num_ctx`) supporting presets from 2,048 up to 262,144 tokens (256K), allowing full utilization of large-context architectures (e.g., Qwen 3.5, Llama 3.1).
- **Installed Models Library**: Modal table listing parameter count, quantization format, file size, and capabilities. Actively reflects the current model with an `ACTIVE` badge, disabled action state, and row highlight.
- **Execution Modes**:
  - **Thinking**: Enables native Chain-of-Thought reasoning.
  - **Fast / No-Think**: Injects directives to bypass reasoning scratchpads for immediate responses.
  - **JSON Mode**: Enforces valid JSON schema formatting via Ollama's grammar-constrained sampler.
  - **Raw Mode**: Bypasses template formatting for direct prompt testing.

### Reasoning Scratchpad & Formatting
- **Chain-of-Thought Scratchpad**: Automatically isolates `<think>` blocks emitted by reasoning models (e.g., DeepSeek R1, Qwen 3.5). Features a stable live timer, token counter, and an in-box copy button.
- **Mathematical Formula Rendering**: LaTeX equations rendered client-side via KaTeX with inline and display math delimiters.
- **Syntax Highlighting**: Code blocks formatted with language headers and one-click copy actions via Highlight.js.
- **Multimodal Support**: Paste or attach images directly into the composer for vision-capable models (LLaVA, MiniCPM-V).
- **Document Export**: One-click export to structured Markdown or JSON, plus clipboard copying.

---

## Quick Start

### Prerequisites

1. **Ollama**: Download and install from [ollama.com](https://ollama.com). Ensure the service is active (`ollama serve` or via the desktop app).
2. **Python 3**: Preinstalled on macOS and Linux; standard installer on Windows.

### Launching the Application

**macOS**:
Double-click `start.command` in Finder, or run in Terminal:
```bash
./start.command
```

**Linux / macOS Terminal**:
```bash
chmod +x start.sh
./start.sh
```

**Windows**:
Double-click `start.bat` or run in Command Prompt:
```cmd
start.bat
```

**Manual Start**:
Run Python's built-in static server from the project directory:
```bash
python3 -m http.server 3300
```
Open your browser to:
```
http://localhost:3300
```

---

## Configuring Ollama CORS

Web browsers enforce Cross-Origin Resource Sharing (CORS) when a web application served from `http://localhost:3300` issues requests to `http://127.0.0.1:11434`.

If Ollama blocks connections with HTTP 403 or network errors, set the `OLLAMA_ORIGINS` environment variable:

### macOS (GUI App)
If Ollama runs as a background menu bar item:
```bash
launchctl setenv OLLAMA_ORIGINS "*"
```
Then quit Ollama completely from the menu bar icon and restart it.

If launching Ollama from Terminal:
```bash
OLLAMA_ORIGINS="*" ollama serve
```

### Linux (systemd)
Edit the service configuration:
```bash
sudo systemctl edit ollama.service
```
Add the following lines:
```ini
[Service]
Environment="OLLAMA_ORIGINS=*"
```
Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Windows
1. Open **System Properties** > **Advanced** > **Environment Variables**.
2. Under User Variables, click **New**.
3. Name: `OLLAMA_ORIGINS`
4. Value: `*`
5. Restart Ollama from the system tray.

---

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Enter` or `Ctrl + Enter` | Send prompt |
| `Shift + Enter` | Insert newline in composer |
| `Escape` | Abort active generation / close active modal |
| `Double-Click` | Inline rename session in ledger |
| `Enter` (while renaming) | Save new session name |
| `Escape` (while renaming) | Cancel session rename |
| `Arrow Up / Down` | Recall previous prompt in an empty composer |

---

## Project Structure

```
ollama-studio/
├── index.html        # Primary single-page application (UI, CSS, JS)
├── chat.html         # Compatibility mirror
├── start.command     # macOS automated launcher
├── start.sh          # Linux / Unix launcher
├── start.bat         # Windows automated launcher
├── .gitignore        # Version control ignore list
├── LICENSE           # MIT License
└── README.md         # Technical documentation
```

---

## License

This project is open-source software licensed under the [MIT License](LICENSE).
