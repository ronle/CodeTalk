"""Configuration for CodeTalk."""
import os

# ── TTS Settings ──────────────────────────────────────────────
# Run: edge-tts --list-voices  to see all options
TTS_VOICE = os.environ.get("CODETALK_VOICE", "en-US-AndrewMultilingualNeural")
TTS_RATE = os.environ.get("CODETALK_RATE", "+5%")  # Just barely faster

# ── Audio Settings ────────────────────────────────────────────
AUDIO_PLAYER = os.environ.get("CODETALK_PLAYER", "powershell")
# Options: "mpv", "ffplay", "powershell"
