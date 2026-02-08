"""
Configuration Manager
=======================

LEARNING POINT: Configuration Management
-------------------------------------------
Hardcoding values (like port numbers, thresholds, file paths) is bad:
  - Changing them requires modifying code
  - Different environments need different values
  - Sensitive values (API keys) end up in version control

Instead, we use a configuration system with layers:

  1. Defaults (hardcoded sensible fallbacks)
  2. Config file (user customizations in YAML)
  3. Environment variables (deployment overrides)

Higher layers override lower layers:
  ENV VARS  →  overrides  →  CONFIG FILE  →  overrides  →  DEFAULTS

LEARNING POINT: YAML
-----------------------
YAML is a human-friendly data format. Compared to JSON:
  - No quotes needed for strings
  - No braces or brackets (uses indentation)
  - Supports comments (JSON doesn't!)

Example YAML:
    voice:
      wake_word: "hey kai"      # The activation phrase
      sample_rate: 16000
      enabled: true
"""

import os
from pathlib import Path
from typing import Any

from kai.utils.logger import setup_logger


logger = setup_logger(__name__)


# Default configuration — used when no config file exists
DEFAULTS = {
    "kai": {
        "name": "Kai",
        "version": "0.1.0",
    },
    "voice": {
        "enabled": True,
        "wake_words": ["hey kai", "kai"],
        "sample_rate": 16000,
        "silence_threshold": 500,
    },
    "speech": {
        "enabled": True,
        "model_size": "base",
        "language": "en",
        "tts_voice": "Samantha",
    },
    "vision": {
        "enabled": True,
        "camera_id": 0,
        "fps": 15,
        "resolution": [640, 480],
        "motion_threshold": 25,
    },
    "io": {
        "data_dir": str(Path.home() / ".kai" / "data"),
        "max_log_size_mb": 50,
    },
}


class Config:
    """
    Layered configuration manager.

    LEARNING POINT: Dot-Notation Access
    --------------------------------------
    Instead of config["voice"]["sample_rate"], you can use:
        config.get("voice.sample_rate")

    This is more readable and handles missing keys gracefully
    (returns a default instead of raising KeyError).

    LEARNING POINT: Singleton Pattern
    ------------------------------------
    There should be only ONE config instance in the entire app.
    We use a class variable (_instance) to ensure this. Every time
    you call Config(), you get the same instance.

    This is the "Singleton" pattern. Use it sparingly — it's
    appropriate for truly global resources like configuration.
    """

    _instance: "Config | None" = None

    def __new__(cls, *args, **kwargs) -> "Config":
        """
        LEARNING POINT: __new__ vs __init__
        --------------------------------------
        __new__ creates the object (called BEFORE __init__).
        __init__ initializes it. By overriding __new__, we can
        return an existing instance instead of creating a new one.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str | Path | None = None):
        if self._initialized:
            return
        self._initialized = True

        self._data: dict = {}
        self._config_path = Path(config_path) if config_path else Path.home() / ".kai" / "config.yaml"

        # Layer 1: Load defaults
        self._data = self._deep_copy(DEFAULTS)

        # Layer 2: Load config file (if exists)
        self._load_file()

        # Layer 3: Apply environment variable overrides
        self._load_env_overrides()

        logger.debug(f"Configuration loaded from: {self._config_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a config value using dot notation.

        LEARNING POINT: Dot-Notation Traversal
        -----------------------------------------
        "voice.sample_rate" gets split into ["voice", "sample_rate"].
        We then walk through the nested dict step by step:
            data["voice"]["sample_rate"]

        If any step fails, we return the default value instead of crashing.

        Args:
            key: Dot-separated path (e.g., "voice.sample_rate")
            default: Value to return if key doesn't exist

        Returns:
            The config value, or default if not found
        """
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a config value using dot notation.

        Creates intermediate dicts as needed:
            config.set("new.nested.key", 42)
            # Creates: {"new": {"nested": {"key": 42}}}
        """
        keys = key.split(".")
        data = self._data

        # Navigate to the parent dict, creating dicts as needed
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def save(self) -> None:
        """Save current configuration to the YAML file."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import yaml
            with open(self._config_path, "w") as f:
                yaml.dump(self._data, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration saved to: {self._config_path}")
        except ImportError:
            # Fallback: save as JSON if PyYAML not installed
            import json
            json_path = self._config_path.with_suffix(".json")
            with open(json_path, "w") as f:
                json.dump(self._data, f, indent=2)
            logger.info(f"Configuration saved as JSON: {json_path}")

    def _load_file(self) -> None:
        """Load configuration from YAML or JSON file."""
        if not self._config_path.exists():
            return

        try:
            import yaml
            with open(self._config_path) as f:
                file_data = yaml.safe_load(f) or {}
            self._deep_merge(self._data, file_data)
        except ImportError:
            # Try JSON fallback
            json_path = self._config_path.with_suffix(".json")
            if json_path.exists():
                import json
                with open(json_path) as f:
                    file_data = json.load(f)
                self._deep_merge(self._data, file_data)

    def _load_env_overrides(self) -> None:
        """
        Apply environment variable overrides.

        LEARNING POINT: Environment Variables
        ----------------------------------------
        Environment variables are key-value pairs set outside your program.
        Convention: KAI_VOICE_SAMPLE_RATE=44100

        We convert this to: {"voice": {"sample_rate": 44100}}

        This is crucial for deployment — you can configure the app
        without modifying any files.
        """
        prefix = "KAI_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # KAI_VOICE_SAMPLE_RATE → voice.sample_rate
                config_key = key[len(prefix):].lower().replace("_", ".")
                # Try to parse as number/bool
                self.set(config_key, self._parse_value(value))

    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parse a string value into the appropriate Python type."""
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> None:
        """
        Deep merge override dict into base dict.

        LEARNING POINT: Recursive Merge
        ----------------------------------
        A shallow merge ({**a, **b}) would replace entire nested dicts.
        Deep merge preserves nested structure:

        base:     {"voice": {"rate": 16000, "channels": 1}}
        override: {"voice": {"rate": 44100}}
        result:   {"voice": {"rate": 44100, "channels": 1}}  ← channels preserved!
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value

    @staticmethod
    def _deep_copy(data: dict) -> dict:
        """Create a deep copy of a nested dict."""
        import copy
        return copy.deepcopy(data)
