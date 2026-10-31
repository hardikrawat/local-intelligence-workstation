# Changelog

All notable changes to **Local Intelligence Workstation (LIW)** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-10-31

### Major Overhaul: Renamed to Local Intelligence Workstation (LIW)
Transitioned the project from a single-engine Ollama chat client into a comprehensive, multi-modality local AI engineering environment coordinating autoregressive language models, diffusion image generators, video motion synthesis, speech recognition, and neural voice synthesis.

### Added
- **Multi-Backend Orchestration Gateway (`server.py`)**:
  - Python standard library gateway supporting concurrent reverse proxies for Ollama (`:11434`), SD WebUI (`:7860`), ComfyUI (`:8188`), Whisper ASR (`:8178`), and Piper TTS (`:5000`).
  - Real-time host hardware telemetry monitoring (macOS `vm_stat`/`sysctl`, Linux `/proc/meminfo`, Windows `wmic`/powershell).
  - Background task worker threads for long-running image and video synthesis, maintaining generation continuity across client disconnects.
  - Tunnel and remote proxy compatibility (automatic ngrok header parsing and dynamic CORS handling).
  - Managed service lifecycle controller (`/api/backends/service/status`, `/start`, `/stop`).
- **Video Synthesis Studio (Motion Generation)**:
  - Text-to-Video and Image-to-Video synthesis pipelines utilizing Stable Video Diffusion (SVD-XT) and AnimateDiff via SD WebUI.
  - Frame rate, motion bucket, fps, and frame count inspector controls.
  - Real-time canvas telemetry displaying step progress, estimated time of arrival (ETA), and backend latency.
  - Interactive stage scrubber featuring frame-by-frame seeking, play/pause controls, looping toggle, and timecode counters.
  - Multi-point synthesis cancellation (`■ STOP`) across inspector, stage header, and centered telemetry banners.
  - Local session clip reel with one-click MP4/WebP downloads and chat studio injection.
- **Image Generation Studio**:
  - Dual-engine diffusion support (SD WebUI `:7860` and ComfyUI `:8188`).
  - Standardized aspect ratio matrix: `1:1 Standard (512x512)`, `1:1 HD (1024x1024)`, `3:4 Portrait (768x1024)`, `16:9 Landscape (1024x576)`.
  - Sampling controls for Euler a, DPM++ 2M Karras, DDIM, UniPC, with CFG scale and seed configuration.
  - Live progressive denoising canvas with centered step telemetry and hardware compute advisories.
  - Synthesis interrupt control (`/api/image/interrupt`).
  - Interactive stage with pan, zoom, full-resolution modal lightbox, and PNG export.
- **Audio Lab (Speech Recognition & Neural TTS)**:
  - Native browser audio capture engine with real-time animated hairline VU meter.
  - Drag-and-drop audio file ingestion for `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, and `.webm`.
  - Integrated waveform scrubber player.
  - Whisper ASR transcription engine with language detection, editable transcripts, and `.txt` export.
  - Piper neural voice synthesizer with multi-voice selection and instant playback.
- **Universal Model Hub & Distribution Gateway**:
  - Tri-repository discovery engine: Ollama Registry, Hugging Face Hub (GGUF), and CivitAI Diffusion Hub.
  - Modality-aware routing separating autoregressive LLMs (with 1-click Ollama pull) from diffusion models (with direct ComfyUI/Forge GGUF download links and terminal `wget` commands).
  - Split-GGUF multi-part shard detection (`-00001-of-00002.gguf`) with visual warning badges to prevent broken downloads.
  - Hugging Face personal access token verification (`/hub/hf/whoami`) and mirror switching (`hf-mirror.com`).
  - Interactive Modelfile builder with 1-click model compilation.
- **Engine Fleet Controller & Preflight Telemetry (`setup.html`)**:
  - Standalone preflight diagnostic dashboard accessible at `/setup`.
  - Step-by-step setup guides for macOS (Apple Silicon), Linux, Windows 11, and Docker.
  - Automated environment flag generation (`OLLAMA_ORIGINS="*"`, `--api --listen`).
- **Workstation Micro-Acoustics (`WorkstationAudio`)**:
  - Procedural sound effect synthesizer utilizing Web Audio API oscillators.
  - Tactical acoustic feedback for mechanical switches, rail switches, completion chimes, and abort thuds.
  - Master volume and mute controls in settings.
- **Workstation Visual Aesthetics & Animations**:
  - Ambient glowing green matrix graph mesh animation during active inference.
  - Fullscreen edge-to-edge workstation bootloader splash screen with developer credit and bypass controls.
  - Instant GPU memory eviction button (`■ PURGE`) broadcasting `keep_alive: 0` to Ollama.
- **Mobile Responsive Workstation Layout**:
  - Balanced 2x2 header command grid maintaining uniform 28px touch targets.
  - Flush 36px single-row prompt bar aligning text input, mic, attachment, and send buttons.
  - Non-collapsing card architecture eliminating layout shifting on mobile viewports.

### Changed
- Migrated default gateway port to `3300` with automated port collision incrementing.
- Synchronized `chat.html` as an exact compatibility mirror of `index.html`.
- Updated all launch automation scripts (`start.sh`, `start.command`, `start.bat`) to launch `server.py`.
- Modernized `docker-compose.yml` with containerized gateway, Ollama, Whisper, and Piper services.

---

## [1.2.0] - 2026-10-28

### Added
- Model Hub integration with live Hugging Face GGUF catalog discovery.
- Dynamic category parsing and search filtering for models.
- Inline status badges for backend verification and ping testing.
- Custom Ollama Modelfile generator dialog.

### Changed
- Overhauled settings modal with tabbed multi-backend configuration.
- Enforced rigid height locks across modal panels to prevent layout shifts.

---

## [1.1.0] - 2026-10-27

### Added
- Classic workstation engineering aesthetic inspired by early Unix consoles and W3C standards.
- Dedicated DeepSeek R1 `<think>` reasoning drawer with generation stopwatch and speed metrics.
- Multimedia lightbox viewer for generated images.
- Precision numeric live animations for token generation counters.

---

## [1.0.0] - 2026-10-25

### Initial Release
- Initial open-source release of Ollama Studio.
- Standalone single-page application with zero-build ES6 architecture.
- Real-time response streaming with native `ReadableStream` chunks.
- Model tag inspection (`/api/tags`), active process monitoring (`/api/ps`), and model details (`/api/show`).
- Local session ledger with browser `localStorage` persistence.