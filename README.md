# Nex - Personal AI Assistant System

> An intelligent, modular assistant inspired by Jarvis — built to see, hear, understand, and act.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![HBOI](https://img.shields.io/badge/HBO--i-Level%204-blueviolet?style=flat-square)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Dashboard UI](#dashboard-ui)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Core Modules](#core-modules)
- [Cyberpunk Dashboard](#cyberpunk-dashboard)
- [Technology Stack](#technology-stack)
- [HBOI Competency Matrix](#hboi-competency-matrix)
- [Design Patterns](#design-patterns)
- [Project Roadmap](#project-roadmap)
- [Getting Started](#getting-started)
- [Running the Dashboard](#running-the-dashboard)
- [Running Tests](#running-tests)
- [License](#license)

---

## Project Overview

**Nex** is a locally-run, privacy-first AI assistant system designed to operate as a personal smart companion. Inspired by systems like Jarvis, Nex integrates multiple recognition pipelines — voice, speech, and motion — into a unified interface that can perceive, interpret, and respond to its environment in real time.

All processing runs **locally on-device**, ensuring full data sovereignty with no dependency on cloud services for core functionality.

### Key Objectives

- Build a real-time voice command and natural language processing pipeline
- Implement computer vision for motion detection and gesture recognition
- Enable local file system read/write operations for persistent memory and context
- Design a modular, extensible architecture that supports future expansion
- Cyberpunk-themed neural dashboard with interactive node-matrix visualization
- Demonstrate professional-grade software engineering at HBOI Level 4

---

## Dashboard UI

Nex ships with a **cyberpunk neural interface** — a dark-mode web dashboard with:

- **Node Matrix** — a live neural network graph where hexagonal nodes represent modules, edges pulse with data flow, and the entire system reacts to voice and gesture input
- **Particle Cloud** — 120 floating particles connected by neural pathways that follow your cursor
- **Thought Cloud** — orbiting thought nodes with elastic mouse-following, visualizing Nex's internal processing
- **System HUD** — module status cards with live waveforms, metric bars, and a command terminal

> Launch it with `python -m nex.ui` and open `http://localhost:3000`

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Nex Core Engine                     │
├──────────┬──────────┬───────────┬────────────────────────┤
│  Voice   │  Speech  │  Vision   │   Local I/O            │
│  Module  │  Module  │  Module   │   Module               │
├──────────┴──────────┴───────────┴────────────────────────┤
│               Event Bus / Message Broker                 │
├──────────────────────────────────────────────────────────┤
│            Plugin & Extension Interface                  │
├──────────────────────────────────────────────────────────┤
│        Cyberpunk Dashboard (Web UI + Node Matrix)        │
└──────────────────────────────────────────────────────────┘
```

The system follows an **event-driven microkernel architecture** where each module operates independently and communicates through a central event bus. This ensures loose coupling, testability, and the ability to hot-swap modules at runtime.

---

## Project Structure

```
Nex/
│
├── nex/                              # Main application package
│   ├── __init__.py                   # Package marker + version
│   ├── __main__.py                   # Entry point (python -m nex)
│   │
│   ├── core/                         # Central system components
│   │   ├── engine.py                 # Orchestrator — manages all modules
│   │   └── event_bus.py              # Pub/Sub event communication system
│   │
│   ├── voice/                        # Audio input processing
│   │   ├── listener.py               # Microphone capture + audio analysis
│   │   └── wake_word.py              # "Hey Nex" wake word detection
│   │
│   ├── speech/                       # Language processing
│   │   ├── recognizer.py             # Speech-to-Text (Whisper STT)
│   │   ├── synthesizer.py            # Text-to-Speech (Nex's voice)
│   │   └── intent.py                 # Intent classification + entity extraction
│   │
│   ├── vision/                       # Camera & visual processing
│   │   ├── camera.py                 # Camera stream management
│   │   ├── motion.py                 # Motion detection (frame differencing)
│   │   └── gesture.py                # Gesture recognition (MediaPipe)
│   │
│   ├── io/                           # File system & configuration
│   │   ├── file_manager.py           # Secure local read/write with path traversal protection
│   │   └── config.py                 # Layered config (YAML + env vars + defaults)
│   │
│   ├── utils/
│   │   └── logger.py                 # Colored terminal logging
│   │
│   └── ui/                           # Cyberpunk Web Dashboard
│       ├── server.py                 # HTTP server + API endpoints
│       └── static/
│           ├── index.html            # Main HUD layout
│           ├── css/style.css         # Cyberpunk dark theme
│           └── js/
│               ├── particles.js      # Neural particle cloud system
│               ├── thoughts.js       # Floating thought node orbits
│               ├── matrix.js         # Node-matrix neural network graph
│               └── app.js            # Dashboard controller + interactions
│
├── tests/                            # Test suite (pytest)
│   ├── test_event_bus.py             # Event system tests
│   ├── test_intent.py                # NLU classification tests
│   ├── test_file_manager.py          # File I/O + security tests
│   └── test_wake_word.py             # Wake word detection tests
│
├── config/
│   └── default.yaml                  # Default configuration
│
├── STRUCTURE.md                      # Detailed structure + data flow diagrams
├── pyproject.toml                    # Project metadata + tool config
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

---

## Core Modules

### [`nex/core/engine.py`](nex/core/engine.py) — The Brain
The central orchestrator that manages all modules through their lifecycle (init → start → stop). Uses the Abstract Base Class pattern to enforce a consistent module interface. Demonstrates **dependency injection**, **composition over inheritance**, and **fault isolation**.

### [`nex/core/event_bus.py`](nex/core/event_bus.py) — The Nervous System
Publish-subscribe event system that decouples all modules. Any module can emit events; any module can listen. Uses `asyncio.gather` for concurrent handler execution and `return_exceptions=True` for fault tolerance. Includes event history for debugging.

### [`nex/voice/listener.py`](nex/voice/listener.py) — The Ears
Captures audio from the microphone, calculates RMS amplitude, and detects when someone is speaking. Runs in simulation mode by default (no microphone needed). Teaches **audio processing**, **async generators**, and **state machines**.

### [`nex/voice/wake_word.py`](nex/voice/wake_word.py) — The Trigger
Detects the activation phrase "Hey Nex" in transcribed text. Extracts the command that follows. Demonstrates the **Single Responsibility Principle** and the **Strategy Pattern** for swappable detection algorithms.

### [`nex/speech/recognizer.py`](nex/speech/recognizer.py) — Speech to Text
Converts audio into text using on-device models (Whisper). Implements **lazy model loading** so the app starts fast and the model loads only on first use. Uses `run_in_executor` to avoid blocking the event loop during ML inference.

### [`nex/speech/synthesizer.py`](nex/speech/synthesizer.py) — Nex's Voice
Converts text responses into spoken audio. Uses macOS's built-in `say` command (cross-platform fallback included). Implements the **Producer-Consumer pattern** with an async queue for orderly speech output.

### [`nex/speech/intent.py`](nex/speech/intent.py) — Understanding Meaning
Classifies user text into structured intents (e.g., `get_time`, `open_file`, `take_note`) with entity extraction. Uses regex-based pattern matching. Teaches **NLU concepts**, **dataclasses**, **regex**, and **Chain of Responsibility**.

### [`nex/vision/camera.py`](nex/vision/camera.py) — The Eyes
Manages camera capture with configurable FPS and resolution. Produces frames for downstream processors. Demonstrates **resource management**, **frame rate control**, and the **Producer pattern**.

### [`nex/vision/motion.py`](nex/vision/motion.py) — Sensing Movement
Detects motion by comparing consecutive frames (background subtraction). Finds contours of moving regions and reports position, size, and intensity. Teaches **frame differencing**, **contour analysis**, and **stateful processing**.

### [`nex/vision/gesture.py`](nex/vision/gesture.py) — Body Language
Recognizes human gestures (wave, stop, thumbs up, point) using MediaPipe pose estimation. Applies temporal smoothing (majority voting over N frames) for reliable detection. Teaches **pose estimation**, **feature engineering**, and **classification**.

### [`nex/io/file_manager.py`](nex/io/file_manager.py) — Memory on Disk
Secure local file read/write with **path traversal prevention**. Validates all paths against the base directory to prevent `../../etc/passwd` attacks. Supports text and JSON, with directory listing via glob patterns.

### [`nex/io/config.py`](nex/io/config.py) — Settings Manager
Layered configuration: defaults → YAML file → environment variables. Supports dot-notation access (`config.get("voice.sample_rate")`). Uses the **Singleton pattern**, **deep merge**, and **environment variable overrides**.

### [`nex/utils/logger.py`](nex/utils/logger.py) — Logging
Color-coded terminal logging with ANSI escape codes. Factory function pattern for consistent logger creation. Supports console + file output with configurable levels.

---

## Cyberpunk Dashboard

The dashboard (`nex/ui/`) is a web-based neural interface with four visual layers:

### [`js/particles.js`](nex/ui/static/js/particles.js) — Neural Particle Cloud
120 floating particles with interconnecting lines, forming a constellation/neural network effect. Particles **follow your cursor** with gentle gravitational attraction. Three neon colors (cyan, magenta, purple) with individual pulse animations and glow effects.

### [`js/thoughts.js`](nex/ui/static/js/thoughts.js) — Thought Cloud Orbits
Task/process nodes that orbit the screen center with elastic spring physics. Nodes have glowing trails, bezier-curved neural pathways connecting them, and **mouse-following behavior** — the entire cloud drifts toward your cursor, simulating "following the thought."

### [`js/matrix.js`](nex/ui/static/js/matrix.js) — Node Matrix Neural Network
The centerpiece: a full neural network graph with 14 hexagonal nodes representing every Nex subsystem (Core, Event Bus, Voice, Speech, NLP, Intent, TTS, Vision, Camera, Motion, Gesture, File I/O, Memory, Config). Features:

- **Hexagonal nodes** with energy levels, glow, and pulsing activation rings
- **Data packets** that travel along edges as glowing orbs
- **Voice reactivity** — nodes breathe outward with audio amplitude
- **Gesture reactivity** — the entire graph shifts in response to detected gestures
- **Mouse interaction** — nearby nodes gravitate toward your cursor
- **Click interaction** — clicking triggers pulse waves and activates nearest node
- **Animated edge flow** — dots travel along connections showing data movement
- **Grid background** that brightens with voice input
- **Corner HUD brackets** for the cyberpunk frame

### [`js/app.js`](nex/ui/static/js/app.js) — Dashboard Controller
Manages the clock, uptime counter, waveform visualizers on module cards, system metrics simulation, thought stream panel, and command input. Bridges user input to the matrix (commands trigger full pipeline animations).

### [`css/style.css`](nex/ui/static/css/style.css) — Cyberpunk Theme
Dark mode design system with CSS custom properties. Features: neon glow effects (box-shadow stacking), scanline overlay animation, vignette, gradient metric bars, HUD-style panels with backdrop blur, and Orbitron/Rajdhani/Share Tech Mono typography.

---

## Technology Stack

| Layer              | Technology                          |
|--------------------|-------------------------------------|
| Language           | Python 3.12+                        |
| Voice Recognition  | Whisper (OpenAI), PyAudio           |
| NLP / LLM          | Local LLM (Ollama / llama.cpp)      |
| TTS                | Piper TTS / macOS `say`             |
| Computer Vision    | OpenCV, MediaPipe                   |
| Event System       | asyncio                             |
| Data Storage       | JSON, YAML                          |
| Dashboard          | Vanilla JS, Canvas API, CSS3        |
| Testing            | pytest, pytest-asyncio              |
| Linting            | Ruff                                |

---

## HBOI Competency Matrix

This project is developed at **HBO-i Level 4 (Professional)**, demonstrating advanced competencies:

| Competency Area              | Level | Demonstration in Nex                                                        |
|------------------------------|-------|-----------------------------------------------------------------------------|
| **Software Design**          | 4     | Event-driven microkernel architecture with plugin extensibility             |
| **Software Realization**     | 4     | Multi-module async system, real-time processing, interactive dashboard      |
| **Software Testing**         | 4     | Unit tests with pytest, parameterized tests, security tests, fixtures       |
| **Software Quality**         | 4     | SOLID principles, 9 design patterns, static analysis with Ruff             |
| **Analysis & Research**      | 4     | ML model evaluation, audio/video pipeline design, trade-off analysis        |
| **Architecture**             | 4     | Modular decomposition, dependency injection, interface-driven design        |
| **Professional Development** | 4     | Agile workflow, comprehensive documentation, version control best practices |
| **User Interaction**         | 4     | Cyberpunk dashboard with real-time visualizations and interactive controls  |

---

## Design Patterns

| Pattern               | Where                                            | Why                                      |
|-----------------------|--------------------------------------------------|------------------------------------------|
| Observer (Pub/Sub)    | [`event_bus.py`](nex/core/event_bus.py)          | Decouple modules from each other         |
| Abstract Base Class   | [`engine.py`](nex/core/engine.py)                | Enforce consistent module interface      |
| Factory               | [`logger.py`](nex/utils/logger.py)               | Consistent logger creation               |
| Singleton             | [`config.py`](nex/io/config.py)                  | One global configuration instance        |
| Strategy              | [`wake_word.py`](nex/voice/wake_word.py)         | Swappable detection algorithms           |
| Template Method       | [`synthesizer.py`](nex/speech/synthesizer.py)    | Customize steps of speech pipeline       |
| Producer-Consumer     | [`synthesizer.py`](nex/speech/synthesizer.py)    | Queue-based orderly speech output        |
| Composition           | [`engine.py`](nex/core/engine.py)                | Engine contains (not inherits) modules   |
| Dependency Injection  | All modules                                      | Dependencies passed in, not created      |

---

## Project Roadmap

### Phase 1 — Foundation
- [x] Project scaffolding and structure
- [x] Core event bus implementation
- [x] Local I/O module (read/write/config)
- [x] Logging and error handling framework
- [x] Unit test suite

### Phase 2 — Voice & Speech
- [x] Audio capture pipeline (simulation mode)
- [x] Wake-word detection
- [x] Speech-to-text integration (Whisper-ready)
- [x] Intent classification engine
- [x] Text-to-speech response system

### Phase 3 — Vision
- [x] Camera stream capture (simulation mode)
- [x] Motion detection pipeline
- [x] Gesture recognition (MediaPipe-ready)
- [x] Pose estimation integration

### Phase 4 — Dashboard & Visualization
- [x] Cyberpunk dark-mode web UI
- [x] Neural particle cloud system
- [x] Node-matrix network visualization
- [x] Voice & gesture reactivity in UI
- [x] Interactive command terminal

### Phase 5 — Integration & Intelligence
- [ ] Cross-module event orchestration (live)
- [ ] Context-aware conversation memory
- [ ] Local LLM integration for reasoning
- [ ] Plugin interface for third-party extensions

### Phase 6 — Polish & Release
- [ ] Real hardware integration (microphone, camera)
- [ ] Performance optimization and profiling
- [ ] Security audit and hardening
- [ ] Packaging and distribution

---

## Getting Started

### Prerequisites

- Python 3.12+
- A microphone (optional — simulation mode works without one)
- A webcam (optional — simulation mode works without one)
- macOS / Linux (primary targets)

### Installation

```bash
git clone https://github.com/Jazziki17/Nex.git
cd Nex
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Nex (Backend)

```bash
python -m nex
```

### Running the Dashboard

```bash
python -m nex.ui
```

Opens automatically at **http://localhost:3000** — a cyberpunk neural interface with live node-matrix visualization, particle clouds, and an interactive command terminal.

### Running Tests

```bash
pytest
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<sub>Built with purpose. Engineered with precision.</sub>
