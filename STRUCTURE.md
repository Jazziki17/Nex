# Project Structure

```
Nex/
│
├── nex/                          # Main application package
│   ├── __init__.py               # Package marker + version info
│   ├── __main__.py               # Entry point (python -m nex)
│   │
│   ├── core/                     # Central system components
│   │   ├── __init__.py
│   │   ├── engine.py             # Orchestrator — manages all modules
│   │   └── event_bus.py          # Pub/Sub communication system
│   │
│   ├── voice/                    # Audio input processing
│   │   ├── __init__.py
│   │   ├── listener.py           # Microphone capture + audio analysis
│   │   └── wake_word.py          # "Hey Nex" detection
│   │
│   ├── speech/                   # Language processing
│   │   ├── __init__.py
│   │   ├── recognizer.py         # Speech-to-Text (Whisper)
│   │   ├── synthesizer.py        # Text-to-Speech (Nex's voice)
│   │   └── intent.py             # Intent classification + entities
│   │
│   ├── vision/                   # Camera & visual processing
│   │   ├── __init__.py
│   │   ├── camera.py             # Camera stream management
│   │   ├── motion.py             # Motion detection (frame differencing)
│   │   └── gesture.py            # Gesture recognition (MediaPipe)
│   │
│   ├── io/                       # File system & configuration
│   │   ├── __init__.py
│   │   ├── file_manager.py       # Secure local read/write
│   │   └── config.py             # Layered config (YAML + env vars)
│   │
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       └── logger.py             # Colored logging setup
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_event_bus.py         # Event system tests
│   ├── test_intent.py            # Intent classification tests
│   ├── test_file_manager.py      # File I/O + security tests
│   └── test_wake_word.py         # Wake word detection tests
│
├── config/
│   └── default.yaml              # Default configuration file
│
├── pyproject.toml                # Project metadata + tool config
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
├── STRUCTURE.md                  # This file
└── README.md                     # Project documentation
```

## Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Microphone │────→│ VoiceListener│────→│ SpeechRecognizer │
└─────────────┘     └──────┬───────┘     └────────┬────────┘
                           │                      │
                    audio.voice_detected    speech.transcribed
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │  Event Bus   │←───→│ IntentClassifier │
                    └──────┬───────┘     └────────┬────────┘
                           │                      │
                           │               intent.classified
                           │                      │
┌─────────────┐     ┌──────▼───────┐     ┌────────▼────────┐
│   Camera    │────→│MotionDetector│     │  FileManager    │
└─────────────┘     └──────┬───────┘     │  (take notes,   │
                           │             │   save state)    │
                  vision.motion_detected  └────────┬────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │   Gesture    │     │ SpeechSynthesizer│
                    │  Recognizer  │     │  (Nex speaks)    │
                    └──────────────┘     └─────────────────┘
```

## Design Patterns Used

| Pattern               | Where                  | Why                                      |
|-----------------------|------------------------|------------------------------------------|
| Observer (Pub/Sub)    | EventBus               | Decouple modules from each other         |
| Abstract Base Class   | Module (engine.py)     | Enforce consistent module interface      |
| Factory               | setup_logger()         | Consistent logger creation               |
| Singleton             | Config                 | One global configuration instance        |
| Strategy              | WakeWordDetector       | Swappable detection algorithms           |
| Template Method       | SpeechSynthesizer      | Customize steps of speech pipeline       |
| Producer-Consumer     | SpeechSynthesizer      | Queue-based orderly speech output        |
| Composition           | NexEngine              | Engine contains (not inherits) modules   |
| Dependency Injection  | All modules            | Dependencies passed in, not created      |

## Key Concepts by File

| File                  | Concepts You'll Learn                              |
|-----------------------|---------------------------------------------------|
| `__main__.py`         | Entry points, async/await, signal handling         |
| `event_bus.py`        | Observer pattern, asyncio.gather, defaultdict      |
| `engine.py`           | ABC, composition, dynamic imports, error isolation |
| `logger.py`           | Logging levels, ANSI colors, factory functions     |
| `listener.py`         | Audio processing, RMS, async generators, simulation|
| `wake_word.py`        | String processing, SRP, any() with generators      |
| `recognizer.py`       | Lazy loading, run_in_executor, encapsulation       |
| `synthesizer.py`      | Queue pattern, subprocess, platform abstraction    |
| `intent.py`           | Regex, dataclasses, NLU concepts, enums            |
| `camera.py`           | Video capture, frame rate control, resource mgmt   |
| `motion.py`           | Frame differencing, contour analysis, state        |
| `gesture.py`          | Pose estimation, feature engineering, smoothing    |
| `file_manager.py`     | pathlib, JSON, security (path traversal), CRUD     |
| `config.py`           | YAML, env vars, singleton, deep merge, dot-notation|
| `test_*.py`           | pytest, fixtures, parametrize, tmp_path, AAA       |
```
