# Local Intelligence Workstation (LIW)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Architecture: Zero--Build](https://img.shields.io/badge/Architecture-Zero--Build%20ES6%20%2B%20Python3-emerald.svg)](#architecture)
[![Platforms: macOS · Linux · Windows · Docker](https://img.shields.io/badge/Platforms-macOS%20·%20Linux%20·%20Windows%20·%20Docker-blueviolet.svg)](#deployment--orchestration)
[![Backends: Multi--Engine](https://img.shields.io/badge/Engines-Ollama%20·%20SD%20WebUI%20·%20ComfyUI%20·%20Whisper%20·%20Piper-orange.svg)](#supported-engines--modalities)

**Local Intelligence Workstation (LIW)** is a professional, high-density local AI engineering environment and multi-modal client interface designed for completely self-hosted artificial intelligence.

Rather than relying on closed cloud APIs, recurring subscriptions, or heavy electron/framework runtimes, Local Intelligence Workstation coordinates multiple independent open-source inference engines into a single unified workstation. It provides dedicated studio workspaces for autoregressive language reasoning, diffusion image generation, motion video synthesis, speech-to-text audio transcription, and neural voice synthesis—with zero data egress.

Designed in accordance with classic workstation aesthetics (inspired by early Unix workstations, Bell Labs engineering consoles, and W3C technical standards), LIW pairs maximum information density and monospace typography with zero-build browser client architecture.

---

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Supported Engines & Modalities](#supported-engines--modalities)
- [Workstation Studios](#workstation-studios)
  - [1. Chat & Reasoning Studio](#1-chat--reasoning-studio)
  - [2. Image Generation Studio](#2-image-generation-studio)
  - [3. Video Synthesis Studio](#3-video-synthesis-studio)
  - [4. Audio Lab (ASR & TTS)](#4-audio-lab-asr--tts)
- [Universal Model Hub](#universal-model-hub)
- [Preflight Fleet Controller (`/setup`)](#preflight-fleet-controller-setup)
- [Workstation Acoustics & Micro-Interactions](#workstation-acoustics--micro-interactions)
- [Deployment & Orchestration](#deployment--orchestration)
  - [Native Execution (macOS / Linux / Windows)](#native-execution)
  - [Turnkey Docker Compose Deployment](#turnkey-docker-compose-deployment)
  - [Remote Access & Tunneling](#remote-access--tunneling)
- [Gateway API Reference](#gateway-api-reference)
- [Configuration Reference](#configuration-reference)
- [Keyboard Shortcuts Reference](#keyboard-shortcuts-reference)
- [Repository Structure](#repository-structure)
- [Security & Air-Gap Compliance](#security--air-gap-compliance)
- [License](#license)

---

## Architectural Overview

Local Intelligence Workstation operates as a client-side engineering canvas served via a lightweight, zero-dependency Python 3 gateway daemon (`server.py`). The gateway concurrently proxies, monitors, and orchestrates local daemons without external npm build systems, webpack bundles, or runtime node dependencies.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           LOCAL INTELLIGENCE WORKSTATION (LIW)                          │
│                   High-Density Technical Engineering Canvas (ES6 / CSS3)                │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ HTTP / REST / Server-Sent Streams
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                server.py · API Gateway                                  │
│  - Multi-Backend Daemon Multiplexer & Latency Prober (/api/backends)                    │
│  - Unified Model Hub Scraper (Ollama Registry · Hugging Face GGUF · CivitAI)           │
│  - Modality-Aware Route Interceptor (Ollama vs ComfyUI/Forge GGUF)                      │
│  - Split-GGUF Multi-Part Shard Verification & Warning Engine                            │
│  - Real-Time Host Hardware Telemetry (macOS vm_stat, Linux /proc/meminfo, Windows wmic) │
│  - Asynchronous Background Workers (Video & Image rendering resilience)                │
└───────┬───────────────────┬───────────────────┬───────────────────┬─────────────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌─────────────────────────────┐
│    Ollama     │   │ SD WebUI /    │   │  Whisper ASR  │   │          Piper TTS          │
│ (Port 11434)  │   │   ComfyUI     │   │ (Port 8178)   │   │         (Port 5000)         │
│  Text LLM &   │   │ (:7860/:8188) │   │ Speech-to-Text│   │     Local Neural Voice      │
│  Multimodal   │   │  Diffusion &  │   │ faster-whisper│   │          Synthesis          │
│    Vision     │   │     Video     │   │               │   │                             │
└───────────────┘   └───────────────┘   └───────────────┘   └─────────────────────────────┘
```

### Key Architectural Tenets

1. **Zero-Build Distribution**: Pure HTML5, modern vanilla ECMAScript 6, and custom CSS design tokens. No `node_modules`, no compilation steps, and no bundling delays.
2. **Deterministic Air-Gap Operation**: Operates 100% offline without remote telemetry, licensing checkpoints, or cloud dependencies.
3. **Decoupled Gateway Layer**: `server.py` relies exclusively on Python's standard library (`http.server`, `urllib`, `threading`, `json`).
4. **Resilient Background Execution**: Long-running image and video synthesis jobs execute within background gateway workers, allowing clients to disconnect or reload without aborting generation state.

---

## Supported Engines & Modalities

| Modality | Primary Engine | Secondary Engine | Default Port | Functional Scope |
|:---|:---|:---|:---|:---|
| **💬 Autoregressive Text & VLM** | **Ollama** (`llama.cpp`) | Custom OpenAI-compatible | `11434` | Text streaming, thinking scratchpads, vision attachments, context sizing |
| **🎨 Diffusion Image Synthesis** | **SD WebUI** (AUTOMATIC1111 / Forge) | **ComfyUI** | `7860` / `8188` | Text-to-Image, Euler/DPM samplers, CFG, seeds, aspect ratio matrix |
| **🎬 Motion Video Generation** | **SD WebUI** (SVD-XT / AnimateDiff) | ComfyUI Video | `7860` | Text-to-Video, Image-to-Video, frame sequencing, WebP/MP4 assembly |
| **🎙️ Speech-to-Text (ASR)** | **faster-whisper** / `whisper.cpp` | Browser Speech API | `8178` | Live microphone dictation, multi-format audio transcription |
| **🔊 Text-to-Speech (TTS)** | **Piper TTS** | Browser Web Speech | `5000` | Real-time neural voice synthesis, multi-voice selection |
| **🌐 Model Discovery & Distribution**| **Universal Model Hub** | Direct HTTP | Gateway | Ollama Registry, Hugging Face Hub (GGUF), CivitAI checkpoints |

---

## Workstation Studios

The client interface is split into specialized modular studios accessible via the primary workstation navigation rail:

```
[◈ CHAT & REASONING]   [⚡ IMAGE STUDIO]   [▶ VIDEO STUDIO]   [🎙 AUDIO LAB]   [🌐 MODEL HUB]
```

---

### 1. Chat & Reasoning Studio

Designed for high-density document ledger interactions, pairing autoregressive response streaming with deep technical telemetry.

- **Chain-of-Thought `<think>` Scratchpad**: Isolates internal reasoning streams (DeepSeek R1, Qwen 2.5) into a dedicated collapsible monospace drawer featuring an active generation stopwatch, live token count, evaluation speed (tokens/sec), and clipboard copy controls.
- **Multimodal Ingestion**: Drag, paste, or browse high-resolution images, source code files, and technical text directly into the prompt composer.
- **`/imagine <prompt>` Slash Command**: Trigger diffusion image synthesis directly inside the conversational ledger without leaving the chat studio.
- **Composer Dictation**: Click the composer microphone icon (or press `Ctrl+M`) to transcribe spoken prompts in real time via Whisper ASR.
- **Auditory Read-Aloud (`Listen`)**: Stream speech playback for any message via Piper neural voices or browser synthesis.
- **Instant VRAM Purge (`■ PURGE`)**: One-click memory eviction that broadcasts `keep_alive: 0` to Ollama, instantly freeing GPU memory.
- **Session Ledger**: Historical conversation ledger with real-time fuzzy search, inline double-click renaming, JSON export, and local storage persistence.

---

### 2. Image Generation Studio

A technical diffusion laboratory optimized for local Stable Diffusion, SDXL, and FLUX inference.

- **Diffusion Inspector**: Configure prompt matrices, negative prompts, checkpoint weights, sampling methods (Euler a, DPM++ 2M Karras, DDIM, UniPC), step counts (1–150), CFG scales (1.0–30.0), and seed values.
- **Standardized Aspect Ratio Presets**: Instant toggle between `1:1 Standard (512x512)`, `1:1 HD (1024x1024)`, `3:4 Portrait (768x1024)`, and `16:9 Landscape (1024x576)`.
- **Progressive Denoising & Live Telemetry**: Centered canvas telemetry displaying current sampling step, elapsed timer, calculated ETA, and live progressive sampler feedback.
- **Stage Canvas & Lightbox**: Interactive viewport with pan, zoom, full-resolution modal lightbox, raw PNG export, base64 clipboard copying, and direct injection into the Chat Studio.
- **Synthesis Interruption (`■ STOP`)**: Immediate cancellation signal dispatch to abort active diffusion passes on the backend.
- **Filmstrip History**: Local thumbnail gallery indexing recent generations with full parameter recall.

---

### 3. Video Synthesis Studio

A high-density motion synthesis suite powered by Stable Video Diffusion (SVD-XT) and AnimateDiff pipelines.

- **Motion Parameters**: Granular control over frame count (8, 12, 16, 24), output frame rate (6–24 fps), motion bucket IDs (1–255), and augmentation levels.
- **Resilient Background Synthesis**: Video generation runs within an asynchronous thread pool in `server.py`. Clients can switch tabs, refresh the browser, or disconnect from mobile without losing active jobs.
- **Interactive Stage Scrubber**: Frame-by-frame scrubbing slider, playback play/pause toggle, looping controller, and timecode counter.
- **Live Canvas Telemetry**: Real-time progress bar, stage counter (`Frame X/Y · Sampling Step A/B`), and backend latency readout.
- **Instant Stop Signal**: Multi-point abort triggers located on the inspector action row, stage action header, and centered telemetry banner.
- **Clip History Reel**: Session reel storing synthesized animations with one-click MP4/WebP downloads and chat sharing.

---

### 4. Audio Lab (ASR & TTS)

A unified acoustic workstation integrating speech recognition and neural voice synthesis.

- **Live VU Audio Recorder**: Browser `MediaRecorder` capture engine with animated hairline VU meter, live millisecond counter, and auto-export.
- **Multi-Format Audio Ingestion**: Drag and drop `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, or `.webm` recordings for instant transcription.
- **Waveform Scrubber**: Interactive visual playback head with click-to-seek waveform navigation.
- **Whisper ASR Pipeline**: Multilingual speech recognition with language override, live transcript editor, clipboard copy, and `.txt` file export.
- **Piper Neural Synthesizer**: On-device neural text-to-speech card with model voice selection, speaking rate adjusters, and live audio generation.

---

## Universal Model Hub

Accessible via the primary rail (`🌐 Model Hub`), LIW includes a unified distribution interface querying three major repositories:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          UNIVERSAL MODEL HUB                           │
├─────────────────────┬──────────────────────────┬───────────────────────┤
│   OLLAMA REGISTRY   │    HUGGING FACE (GGUF)   │    CIVITAI DIFFUSION  │
│  - Live registry    │  - Pipeline categories   │  - SD Checkpoints     │
│  - Tag resolution   │  - Modality router       │  - LoRAs & VAEs       │
│  - 1-click pull     │  - Split-shard warning   │  - Safetensors DL     │
│  - Bandwidth meter  │  - Modelfile generator   │  - Base model tags    │
└─────────────────────┴──────────────────────────┴───────────────────────┘
```

### 1. Ollama Registry Scraper
- Real-time catalog search across `ollama.com`.
- Inspect model parameter variants, context sizes, and quantization tags.
- One-click native pulling with live streaming download percentage and MB/s rate tracking.

### 2. Hugging Face Hub (GGUF Distribution Engine)
- Real-time discovery across tens of thousands of community models.
- **Modality-Aware Pipeline Routing**:
  - **Autoregressive Models (LLMs / VLMs)**: Provides 1-click pull syntax for Ollama (`ollama run hf.co/...`), custom Modelfile creation, and quantization pickers (`Q4_K_M`, `Q5_K_M`, `Q8_0`).
  - **Diffusion Checkpoints (FLUX / SDXL GGUF)**: Flags models requiring diffusion architectures. Provides copyable terminal `wget` commands and direct download paths targeting `ComfyUI/models/diffusion_models/` or `models/unet/`.
- **Split-GGUF Multi-Part Shard Detection**: Automatically analyzes model file trees. Multi-part split files (`-00001-of-00002.gguf`) receive technical alert badges warning that direct single-file pulling will fail, recommending single-file quantizations.
- **Token Verification & Regional Mirrors**: Built-in authentication probe (`/hub/hf/whoami`) and one-click mirror switching between `huggingface.co` and `hf-mirror.com`.

### 3. CivitAI Discovery
- Direct catalog query for Stable Diffusion checkpoints, LoRAs, and VAEs.
- Clear metadata tags identifying base architectures (`SD 1.5`, `SDXL 1.0`, `Pony`, `FLUX.1 D`).
- Direct safetensors download links and full prompt inspection.

---

## Preflight Fleet Controller (`/setup`)

Navigate to `http://localhost:3300/setup` (or click **SETUP ↗** in the status footer) to launch the **Engine Fleet Controller**:

- **Automated Daemon Health Diagnostics**: Probes connectivity and response latency across Ollama, SD WebUI, ComfyUI, Whisper, and Piper.
- **Operating System Installation Guides**: Interactive platform guides (macOS Apple Silicon, Ubuntu / Debian Linux, Windows 11, Docker) detailing exact commands to install, configure, and launch every inference engine.
- **Environment & CORS Configuration**: Automatic generation of environment flags (`OLLAMA_ORIGINS="*"`, `--api --listen`, `--cors-allow-origins="*"`) required for seamless local daemon communication.
- **Process Lifecycle Management**: Gateway controls to start, inspect, or restart local background services.

---

## Workstation Acoustics & Micro-Interactions

Built upon a vintage terminal micro-acoustics engine (`WorkstationAudio`), LIW provides tactile audio-frequency feedback generated via the browser's native Web Audio API (zero external sound samples required):

- **Mechanical Key Switch Clicks**: Subtle click pulses on interactive toggles and command inputs.
- **Chirp Mode Switches**: Dual-tone frequency shifts during studio rail tab transitions.
- **Telemetry Blips**: Resonant high-frequency chimes upon inference milestone completion.
- **Abort Thuds**: Low-frequency resonant thuds when canceling operations or purging VRAM.
- **Customizable**: Configurable volume slider and global mute switch accessible in `Settings > Acoustics`.

---

## Deployment & Orchestration

### Native Execution

#### Prerequisites
- **Python 3.8+** (Uses standard library only; zero `pip install` required)
- At least one inference backend (e.g., [Ollama](https://ollama.com))

#### Launch Commands

```bash
# Clone the repository
git clone https://github.com/hardikrawat/local-intelligence-workstation.git
cd local-intelligence-workstation

# macOS / Linux
chmod +x start.sh start.command
./start.sh

# macOS Finder One-Click
Double-click start.command

# Windows
start.bat

# Direct Python Invocation (specify port if desired)
python3 server.py 3300
```

Open `http://localhost:3300` in your web browser.

---

### Turnkey Docker Compose Deployment

To orchestrate the workstation along with containerized inference backends in one command:

```bash
# Start all containerized services
docker compose up -d

# Inspect running containers
docker compose ps

# Follow gateway logs
docker compose logs -f workstation
```

#### Services Spawned:
- `liw-gateway`: Workstation Web Gateway & UI (`http://localhost:3300`)
- `liw-ollama`: Autoregressive LLM & Vision Engine (`http://localhost:11434`)
- `liw-whisper`: Faster-Whisper ASR Speech-to-Text Service (`http://localhost:8178`)
- `liw-piper`: Piper Neural Text-to-Speech Engine (`http://localhost:5000`)

---

### Remote Access & Tunneling

To access your workstation from a mobile device or remote computer:

1. **Local Area Network (LAN)**: The gateway binds to `0.0.0.0`. Navigate to `http://<HOST_IP>:3300` from any device on your local network.
2. **ngrok Secure Tunnel**:
   ```bash
   ngrok http 3300
   ```
   The LIW gateway automatically detects and permits requests bypassing standard CORS and ngrok browser warning headers (`--ngrok-skip-browser-warning`).
3. **Tailscale / VPN**: Seamlessly access your workstation securely across private mesh networks.

---

## Gateway API Reference

The gateway daemon (`server.py`) provides structured JSON REST endpoints:

### Daemon Health & Telemetry
| Endpoint | Method | Description |
|:---|:---|:---|
| `/api/backends` | `GET` | Probe status, latency, and active URLs of all inference backends |
| `/api/backends/service/status` | `GET` | Inspect process lifecycle status of a managed daemon |
| `/api/backends/service/start` | `POST` | Spawn a managed background inference daemon |
| `/api/backends/service/stop` | `POST` | Terminate a managed background daemon |
| `/api/system/memory` | `GET` | Real-time host RAM utilization (Total, Used, Free, Active, Inactive) |

### Studios & Inference Dispatch
| Endpoint | Method | Description |
|:---|:---|:---|
| `/api/image/generate` | `POST` | Asynchronous diffusion image synthesis request |
| `/api/image/status` | `GET` | Poll active image rendering job status, progress, and stage |
| `/api/image/interrupt` | `POST` | Abort active diffusion pass on image backend |
| `/api/video/generate` | `POST` | Dispatch motion video synthesis job to background worker |
| `/api/video/status` | `GET` | Poll motion synthesis progress, frame counter, and result clip |
| `/api/video/interrupt` | `POST` | Interrupt running video generation job |
| `/api/audio/transcribe` | `POST` | Transcribe multipart audio payload via Whisper ASR |
| `/api/audio/synthesize` | `POST` | Generate neural speech audio stream via Piper TTS |
| `/api/chat/resume` | `GET` | Reconnect to active stream after network interruption |

### Universal Model Hub
| Endpoint | Method | Description |
|:---|:---|:---|
| `/hub/ollama/search` | `GET` | Scrape and query Ollama model library with metadata |
| `/hub/ollama/tags` | `GET` | Retrieve available quantization tags for an Ollama model |
| `/hub/hf/search` | `GET` | Query Hugging Face Hub API for GGUF model repositories |
| `/hub/hf/model` | `GET` | Detailed model tree inspection with split-shard validation |
| `/hub/hf/whoami` | `GET` | Validate Hugging Face personal access token and user scopes |
| `/hub/civitai/search` | `GET` | Search CivitAI checkpoint and LoRA model databases |
| `/hub/categories` | `GET` | Fetch dynamic category trees from upstream registries |

---

## Configuration Reference

Custom daemon URLs and parameters persist in `backends.json` in the root workspace directory:

```json
{
  "ollama": "http://127.0.0.1:11434",
  "sd_webui": "http://127.0.0.1:7860",
  "comfyui": "http://127.0.0.1:8188",
  "whisper": "http://127.0.0.1:8178",
  "piper": "http://127.0.0.1:5000",
  "hf_token": "",
  "hf_endpoint": "https://huggingface.co"
}
```

Client preferences (themes, active studio, reasoning expansion, audio volume) are saved strictly to the browser's `localStorage` and never transmitted across the network.

---

## Keyboard Shortcuts Reference

| Shortcut | Context | Action |
|:---|:---|:---|
| `Enter` / `Ctrl + Enter` | Composer | Send prompt / execute generation |
| `Shift + Enter` | Composer | Insert newline |
| `Escape` | Global | Abort active generation / close active modal |
| `Ctrl + M` / `Cmd + M` | Composer | Toggle Whisper ASR microphone dictation |
| `Ctrl + /` / `Cmd + /` | Global | Focus prompt composer |
| `Double-Click` | Session Ledger | Rename chat session inline |
| `Enter` (Renaming) | Session Ledger | Save new session title |
| `Escape` (Renaming) | Session Ledger | Discard rename changes |
| `Arrow Up` / `Down` | Empty Composer | Recall previous prompt from session history |

---

## Repository Structure

```
local-intelligence-workstation/
├── index.html              # Primary single-page application (Canvas, Studios, CSS, JS)
├── chat.html               # Dedicated compatibility mirror
├── setup.html              # Preflight Fleet Controller & diagnostics dashboard
├── server.py               # Zero-dependency API gateway daemon & proxy
├── docker-compose.yml      # Multi-backend container orchestration specification
├── start.sh                # Unix / Linux launch automation script
├── start.command           # macOS Finder one-click executable launcher
├── start.bat               # Windows batch launcher script
├── .gitignore              # Git ignore specification
├── CHANGELOG.md            # Comprehensive version history & release notes
├── LICENSE                 # MIT License specification
└── README.md               # Technical workstation documentation & architecture
```

---

## Security & Air-Gap Compliance

Local Intelligence Workstation is engineered for environments with strict data governance:

- **Zero Cloud Egress**: Prompts, generated imagery, audio recordings, and model weights stay strictly on your local hardware.
- **Air-Gapped Operation**: Functions seamlessly on isolated machines without an active internet connection.
- **No Third-Party Analytics**: Contains zero external tracking pixels, CDN dependencies, or phone-home beacons.
- **Direct Daemon Proxies**: All inference communications route through `server.py` directly to localhost daemons.

---

## License

This project is open-source software licensed under the **[MIT License](LICENSE)**.

Copyright &copy; 2026 Hardik Rawat.