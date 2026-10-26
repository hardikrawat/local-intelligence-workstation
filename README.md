# Ollama Studio

A lightweight, zero-build web interface for interacting with local LLMs via [Ollama](https://ollama.com).

Ollama Studio runs entirely in the browser as a standalone single-page application. It requires no Node.js toolchains, build steps, or backend databases—just a static file server (like Python's built-in `http.server`) to serve the client assets.

---

## Architecture & How It Works

Ollama Studio communicates directly with the local Ollama REST server running at `http://127.0.0.1:11434`.

```
┌─────────────────────────────────┐          REST / Streams          ┌──────────────────────────┐
│          Browser UI             │ ───────────────────────────────> │      Ollama Daemon       │
│  (index.html · HTML5 / CSS3 / JS)│ <─────────────────────────────── │  (http://127.0.0.1:11434) │
└─────────────────────────────────┘   /api/chat, /api/ps, /api/show  └──────────────────────────┘
                 │
                 ▼
       Browser localStorage
   (sessions, presets, settings)
```

- **Client-Side Only**: Runs from static files. Conversations, model presets, and UI preferences are stored in the browser's `localStorage`. No data is ever sent to external cloud servers.
- **Direct API Integration**: Utilizes Ollama's HTTP endpoints:
  - `/api/tags` to discover locally installed models.
  - `/api/ps` to monitor running models and VRAM residency in real time.
  - `/api/show` to inspect model architecture, parameter size, context length, and quantization details.
  - `/api/chat` with `ReadableStream` for chunked response streaming.
  - `/api/generate` with `keep_alive: 0` for immediate VRAM eviction.
  - `/api/pull` with progress streaming for downloading models.

---

## Key Features

- **Live Generation Telemetry**: Computes and displays Time to First Token (TTFT), real-time generation speed (tokens/sec), prompt evaluation count, and total duration from Ollama's stream metadata.
- **VRAM Residency & Eviction**: Polls `/api/ps` to show which model is loaded in GPU memory and provides an instant "Evict" button (`keep_alive: 0`) to release VRAM without restarting Ollama.
- **Native Chain-of-Thought (<think> Tags)**: Automatically parses `<think>` reasoning blocks from reasoning models (e.g., DeepSeek R1). Reasoning scratchpads are rendered in an expandable collapsible panel.
- **Execution Modes**:
  - **Thinking**: Enables native reasoning blocks and adjusts temperature for chain-of-thought workflows.
  - **Fast / No-Think**: Injects system directives and parameters to bypass reasoning scratchpads for quick answers.
  - **JSON Mode**: Sends `format: "json"` to Ollama's sampler to enforce valid JSON syntax.
  - **Raw Passthrough**: Bypasses system prompt templating (`raw: true`).
  - **Multimodal / Vision**: Base64 image attachment support for vision models (LLaVA, MiniCPM-V, etc.).
- **Rich Rendering**:
  - Markdown formatting via Marked.js (tables, task lists, blockquotes).
  - Syntax highlighting with language detection and one-click copy buttons via Highlight.js.
  - LaTeX scientific formulas and equations via KaTeX auto-render.
- **Session Management**: Multi-chat sidebar with search, auto-titling based on prompt context, conversation cloning, and export to Markdown or JSON.
- **Dual Themes & Eco Mode**: Includes an archival light theme, an obsidian dark theme, and an optional Eco Mode that disables ambient CSS animations on low-power devices.

---

## Quick Start

### Prerequisites

1. **Ollama**: Download and install from [ollama.com](https://ollama.com). Ensure it is running (`ollama serve` or via the menu bar app).
2. **Python 3**: Preinstalled on macOS and modern Linux distributions; standard installer on Windows.

### Launching the Application

**macOS**:
Double-click `start.command` in Finder, or run:
```bash
./start.command
```

**Linux / macOS Terminal**:
```bash
chmod +x start.sh
./start.sh
```

**Windows**:
Double-click `start.bat` or run:
```cmd
start.bat
```

**Manual Start**:
Start any static file server from the project directory and open your browser:
```bash
python3 -m http.server 3300
```
Then navigate to:
```
http://localhost:3300
```

---

## Configuring Ollama CORS

Browsers enforce Cross-Origin Resource Sharing (CORS) when a web application running on `http://localhost:3300` sends HTTP requests to `http://127.0.0.1:11434`.

If Ollama rejects connections or shows a network error in the console, configure `OLLAMA_ORIGINS`:

### macOS (GUI App)
If Ollama runs as a background menu bar application:
```bash
launchctl setenv OLLAMA_ORIGINS "*"
```
Then quit Ollama completely from the menu bar and reopen it.

If running Ollama directly from the terminal:
```bash
OLLAMA_ORIGINS="*" ollama serve
```

### Linux (systemd)
Edit the service configuration:
```bash
sudo systemctl edit ollama.service
```
Add the following lines under the `[Service]` section:
```ini
[Service]
Environment="OLLAMA_ORIGINS=*"
```
Reload and restart the service:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Windows
1. Open **System Properties** > **Advanced** > **Environment Variables**.
2. Under User or System variables, click **New**.
3. Variable name: `OLLAMA_ORIGINS`
4. Variable value: `*`
5. Restart Ollama from the system tray.

---

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Enter` | Send prompt (when input is focused) |
| `Shift + Enter` | Insert newline |
| `Escape` | Close active modal / abort current generation |
| `Arrow Up / Down` | In an empty input field, cycle through sent prompts |

---

## Project Structure

```
ollama-studio/
├── index.html        # Main application interface and client logic
├── chat.html         # Compatibility entry point
├── start.command     # macOS launcher script
├── start.sh          # Linux and Unix launcher script
├── start.bat         # Windows launcher script
├── .gitignore        # Git ignore rules
├── LICENSE           # MIT License
└── README.md         # Documentation
```

---

## License

This project is licensed under the [MIT License](LICENSE).
