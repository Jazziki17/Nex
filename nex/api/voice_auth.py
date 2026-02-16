"""
Voice Authentication — Speaker verification using resemblyzer.

Uses a pre-trained d-vector model to generate 256-dim speaker embeddings.
Cosine similarity between enrollment and live audio determines match.
"""

from pathlib import Path

import numpy as np

from nex.utils.logger import setup_logger

logger = setup_logger(__name__)

PROFILE_DIR = Path.home() / ".nex" / "data"
PROFILE_FILE = PROFILE_DIR / "voice_profile.npy"

SIMILARITY_THRESHOLD = 0.75
SAMPLE_RATE = 16000


class VoiceAuth:
    """Speaker verification using resemblyzer d-vector embeddings."""

    def __init__(self):
        self._encoder = None
        self._profile: np.ndarray | None = None
        self._load_profile()

    def _get_encoder(self):
        """Lazy-load the resemblyzer encoder."""
        if self._encoder is None:
            from resemblyzer import VoiceEncoder
            self._encoder = VoiceEncoder()
            logger.info("VoiceEncoder loaded")
        return self._encoder

    def _load_profile(self):
        """Load saved voice profile from disk."""
        if PROFILE_FILE.exists():
            try:
                self._profile = np.load(str(PROFILE_FILE))
                logger.info("Voice profile loaded")
            except Exception as e:
                logger.warning(f"Failed to load voice profile: {e}")
                self._profile = None

    def is_enrolled(self) -> bool:
        return self._profile is not None

    def enroll(self, audio_samples: list[np.ndarray]) -> str:
        """Enroll a speaker from multiple audio samples.

        Args:
            audio_samples: List of float32 numpy arrays (16kHz mono).

        Returns:
            Status message.
        """
        if len(audio_samples) < 1:
            return "Error: need at least one audio sample to enroll."

        encoder = self._get_encoder()
        from resemblyzer import preprocess_wav

        embeddings = []
        for audio in audio_samples:
            wav = preprocess_wav(audio, source_sr=SAMPLE_RATE)
            embed = encoder.embed_utterance(wav)
            embeddings.append(embed)

        # Average embeddings for a robust profile
        self._profile = np.mean(embeddings, axis=0)

        # Save to disk
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        np.save(str(PROFILE_FILE), self._profile)
        logger.info(f"Voice profile enrolled from {len(audio_samples)} samples")
        return f"Voice enrolled successfully from {len(audio_samples)} samples."

    def verify(self, audio: np.ndarray) -> tuple[bool, float]:
        """Verify a speaker against the enrolled profile.

        Args:
            audio: Float32 numpy array (16kHz mono).

        Returns:
            (is_match, confidence) tuple.
        """
        if self._profile is None:
            return True, 1.0  # Not enrolled = allow all

        encoder = self._get_encoder()
        from resemblyzer import preprocess_wav

        wav = preprocess_wav(audio, source_sr=SAMPLE_RATE)
        embed = encoder.embed_utterance(wav)

        # Cosine similarity
        similarity = float(np.dot(self._profile, embed) / (
            np.linalg.norm(self._profile) * np.linalg.norm(embed)
        ))

        is_match = similarity >= SIMILARITY_THRESHOLD
        logger.info(f"Voice verification: similarity={similarity:.3f}, match={is_match}")
        return is_match, similarity

    def reset(self) -> str:
        """Delete voice profile and disable voice auth."""
        self._profile = None
        if PROFILE_FILE.exists():
            PROFILE_FILE.unlink()
            logger.info("Voice profile deleted")
        return "Voice authentication reset. All voices will be accepted."
