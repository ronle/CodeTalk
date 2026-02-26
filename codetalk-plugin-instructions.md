# CodeTalk — Plugin Build Instructions

## Philosophy

CodeTalk adds a **spoken reflection layer** to Claude Code CLI. But the core design principle is restraint. The voice should feel like a real colleague sitting next to you — someone who's quiet most of the time, occasionally says something genuinely useful, and knows when to shut up.

**Silence is the default. Speech is the exception.**

If the user ever feels like "here it goes again," the plugin has failed. The moment the voice becomes predictable, performative, or hollow — people turn it off and never come back. Every reflection must earn its airtime.

### What Natural Means

A real colleague **wouldn't**:
- Comment on every single thing you do
- Start talking the instant you stop typing
- Always take the same time to "think"
- Sound like they had a prepared script
- Say "nice refactor" (empty praise)

A real colleague **would**:
- Be quiet most of the time
- Only speak when they spotted something worth mentioning
- Pause before speaking, like they're actually thinking
- Vary in length — sometimes one sentence, sometimes a few
- Occasionally say nothing even when they *could* say something

The 2-3 second delay after Claude finishes writing isn't a bug — it **is** the natural thinking pause. Don't try to optimize it away.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Code CLI                                            │
│                                                             │
│  1. Claude generates response on screen (normal behavior)   │
│                                                             │
│  2. Stop hook fires                                         │
│     ├── Reads transcript → extracts last response           │
│     ├── GATE: Should I speak? (most of the time: no)        │
│     │   ├── Too short? → silence                            │
│     │   ├── Mostly code? → silence                          │
│     │   ├── Simple Q&A? → silence                           │
│     │   ├── Randomness check (skip ~30% even if worthy)     │
│     │   └── Pass all gates? → continue                      │
│     ├── Sends to Haiku with strict reflection prompt         │
│     │   └── Haiku can also return SKIP (silence)            │
│     ├── Receives reflection text                            │
│     └── edge-tts → plays audio                              │
│                                                             │
│  3. User hears a brief, genuine remark — or nothing at all  │
└─────────────────────────────────────────────────────────────┘
```

Target: voice activates on roughly **20-35% of responses**. The user should never be able to predict when it will speak.

---

## Prerequisites

| Requirement | Purpose | Install |
|-------------|---------|---------|
| Claude Code CLI | Base tool | Already installed |
| Python 3.10+ | Hook scripts & TTS | Already on system |
| `edge-tts` | Free neural TTS | `pip install edge-tts` |
| `anthropic` | Reflection LLM call | `pip install anthropic` |
| Anthropic API key | For Haiku calls | `ANTHROPIC_API_KEY` env var |
| `mpv` | Audio playback | `choco install mpv` (or `ffplay`) |

### Verify edge-tts

```powershell
pip install edge-tts
edge-tts --text "Testing voice" --write-media test.mp3
mpv test.mp3
```

---

## Plugin Structure

```
codetalk/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   ├── hooks.json
│   └── codetalk.py              # Main hook — the gatekeeper
├── scripts/
│   ├── generate_reflection.py   # LLM reflection call
│   ├── speak.py                 # edge-tts playback
│   └── config.py                # All settings
└── README.md
```

---

## Step 1 — Plugin Manifest

**File: `.claude-plugin/plugin.json`**

```json
{
  "name": "codetalk",
  "description": "Your code talks to you — occasional spoken reflections on Claude's output, restrained and natural",
  "version": "1.0.0",
  "author": {
    "name": "Ron"
  }
}
```

---

## Step 2 — Configuration

**File: `scripts/config.py`**

```python
"""Configuration for CodeTalk."""
import os

# ── LLM Settings ──────────────────────────────────────────────
REFLECTION_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 150  # Short. Reflections aren't speeches.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── TTS Settings ──────────────────────────────────────────────
# Run: edge-tts --list-voices  to see all options
TTS_VOICE = os.environ.get("CODETALK_VOICE", "en-US-GuyNeural")
TTS_RATE = os.environ.get("CODETALK_RATE", "+5%")  # Just barely faster

# ── Gatekeeper Settings ───────────────────────────────────────
# These gates exist to make silence the default.

# Minimum chars to even consider speaking
MIN_RESPONSE_LENGTH = 300

# If response is more than this ratio of code blocks, stay quiet
MAX_CODE_RATIO = 0.70

# Random skip probability (0.0 to 1.0)
# Even when all other gates pass, skip this % of the time.
# This prevents the voice from feeling predictable.
# 0.30 = stay silent 30% of the time even on "worthy" responses
RANDOM_SKIP_CHANCE = 0.30

# Cooldown: minimum seconds between reflections.
# Prevents rapid-fire commentary during fast back-and-forth.
COOLDOWN_SECONDS = 120  # 2 minutes minimum between voice reflections

# Maximum response chars to send to Haiku (cost control)
MAX_RESPONSE_CHARS = 3000

# ── Audio Settings ────────────────────────────────────────────
AUDIO_PLAYER = os.environ.get("CODETALK_PLAYER", "mpv")
# Options: "mpv", "ffplay", "powershell"

# Path to cooldown state file
COOLDOWN_FILE = os.path.join(
    os.path.expanduser("~"), ".claude", "codetalk-last-spoke.txt"
)

# ── The Reflection Prompt ─────────────────────────────────────
# This is the most important part of the entire plugin.
# It defines personality, restraint, and what "worth saying" means.

REFLECTION_SYSTEM_PROMPT = """You sometimes provide a brief spoken aside after 
a coding assistant finishes writing a response on screen. You are NOT a 
narrator. You are NOT a summarizer. You don't repeat what's on screen.

You're more like a colleague who was watching over the shoulder and 
occasionally has a genuine observation. Most of the time, you'd say nothing. 
But sometimes you notice something worth mentioning:

- A non-obvious trade-off in the approach taken
- A subtle risk or gotcha the user might miss
- The real reason behind a design choice (the "why behind the why")
- Something that connects to a bigger picture
- A genuinely useful "watch out for..." that isn't already stated

You speak in 1-3 sentences. Never more. Your tone is casual, unhurried, like 
you're thinking out loud. You don't use filler phrases. You don't start with 
"So" or "Alright" or "Just to note." You get to the point.

CRITICAL RULES:
- If you don't have a genuine, non-obvious insight → respond with exactly: SKIP
- If the written response already covers everything well → SKIP
- If your comment would just be a restatement in different words → SKIP
- If your observation is generic ("nice approach", "looks clean") → SKIP
- SKIP is always the safer choice. Only speak when you'd genuinely tap 
  someone on the shoulder for this.
- Never reference that you're a voice or a plugin or a companion.
- Never say "I noticed" or "I see that" — just state the observation directly.
- Vary your sentence structure. Don't fall into a pattern."""
```

Key design decisions:
- **`RANDOM_SKIP_CHANCE = 0.30`**: Even "worthy" responses get skipped 30% of the time. This makes the voice unpredictable.
- **`COOLDOWN_SECONDS = 120`**: Minimum 2 minutes between reflections. No rapid-fire.
- **The prompt heavily defaults to SKIP.** Haiku is instructed that silence is always the safer choice.

---

## Step 3 — Reflection Generator

**File: `scripts/generate_reflection.py`**

```python
"""Generate a verbal reflection — or decide to stay silent."""
import sys
import json
import anthropic
from config import (
    REFLECTION_MODEL, MAX_TOKENS, ANTHROPIC_API_KEY,
    REFLECTION_SYSTEM_PROMPT, MAX_RESPONSE_CHARS
)


def generate_reflection(response_text: str) -> str | None:
    """Ask Haiku for a reflection. Returns None if it decides to stay quiet."""
    if not ANTHROPIC_API_KEY:
        print("WARN: No ANTHROPIC_API_KEY set", file=sys.stderr)
        return None

    trimmed = response_text[:MAX_RESPONSE_CHARS]
    if len(response_text) > MAX_RESPONSE_CHARS:
        trimmed += "\n[...truncated...]"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=REFLECTION_MODEL,
        max_tokens=MAX_TOKENS,
        system=REFLECTION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Here is what was just written on screen. "
                    "Provide a brief spoken aside — or SKIP if there's "
                    "nothing genuinely worth saying out loud.\n\n"
                    f"{trimmed}"
                )
            }
        ]
    )

    reflection = message.content[0].text.strip()

    # Haiku returned SKIP (or variations)
    if reflection.upper().startswith("SKIP"):
        return None

    # Safety: if somehow it returned something very long, it's not natural
    if len(reflection) > 500:
        return None

    return reflection


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    result = generate_reflection(text)
    if result:
        print(result)
    else:
        print("(silence)", file=sys.stderr)
        sys.exit(1)
```

---

## Step 4 — TTS Speaker

**File: `scripts/speak.py`**

```python
"""Convert text to speech and play it."""
import asyncio
import sys
import os
import tempfile
import subprocess
from config import TTS_VOICE, TTS_RATE, AUDIO_PLAYER


async def speak(text: str):
    """Generate audio and play it."""
    import edge_tts

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
        await communicate.save(tmp_path)

        if AUDIO_PLAYER == "mpv":
            subprocess.run(
                ["mpv", "--no-video", "--really-quiet", tmp_path],
                timeout=30
            )
        elif AUDIO_PLAYER == "ffplay":
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                 tmp_path],
                timeout=30
            )
        elif AUDIO_PLAYER == "powershell":
            ps_cmd = (
                f'Add-Type -AssemblyName presentationCore; '
                f'$p = New-Object System.Windows.Media.MediaPlayer; '
                f'$p.Open("{tmp_path}"); '
                f'Start-Sleep -Milliseconds 500; '
                f'$p.Play(); '
                f'Start-Sleep -Seconds '
                f'([math]::Ceiling($p.NaturalDuration.TimeSpan.TotalSeconds) '
                f'+ 1); $p.Close()'
            )
            subprocess.run(["powershell", "-Command", ps_cmd], timeout=30)
        else:
            if os.name == 'nt':
                os.startfile(tmp_path)
            else:
                subprocess.run(["xdg-open", tmp_path])
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read().strip()
    if text:
        asyncio.run(speak(text))
```

---

## Step 5 — The Main Hook (The Gatekeeper)

**File: `hooks/codetalk.py`**

This is where restraint lives. Multiple gates must be passed before the voice activates.

```python
#!/usr/bin/env python3
"""
CodeTalk — Stop hook for Claude Code.

The gatekeeper. Most of the time, this script does nothing.
That's by design.
"""
import json
import sys
import os
import re
import random
import time

# Add scripts dir to path
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', 'scripts')
sys.path.insert(0, SCRIPT_DIR)

from config import (
    MIN_RESPONSE_LENGTH, MAX_CODE_RATIO,
    RANDOM_SKIP_CHANCE, COOLDOWN_SECONDS, COOLDOWN_FILE
)
from generate_reflection import generate_reflection
from speak import speak
import asyncio


def extract_last_response(transcript_path: str) -> str | None:
    """Pull Claude's last response from the transcript JSONL."""
    if not os.path.exists(transcript_path):
        return None

    last_assistant_text = None

    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get('role') == 'assistant':
                    content = entry.get('content', [])
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and \
                                block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    if text_parts:
                        last_assistant_text = '\n'.join(text_parts)
            except json.JSONDecodeError:
                continue

    return last_assistant_text


def code_ratio(text: str) -> float:
    """What fraction of the response is fenced code blocks."""
    blocks = re.findall(r'```[\s\S]*?```', text)
    code_len = sum(len(b) for b in blocks)
    return code_len / max(len(text), 1)


def is_on_cooldown() -> bool:
    """Check if we spoke too recently."""
    try:
        if os.path.exists(COOLDOWN_FILE):
            with open(COOLDOWN_FILE, 'r') as f:
                last_spoke = float(f.read().strip())
            return (time.time() - last_spoke) < COOLDOWN_SECONDS
    except (ValueError, OSError):
        pass
    return False


def record_spoke():
    """Mark that we just spoke."""
    try:
        os.makedirs(os.path.dirname(COOLDOWN_FILE), exist_ok=True)
        with open(COOLDOWN_FILE, 'w') as f:
            f.write(str(time.time()))
    except OSError:
        pass


def should_even_consider(text: str) -> bool:
    """
    The gates. Each one is a reason to stay silent.
    Order matters — cheapest checks first.
    """

    # Gate 1: Too short. Nothing substantial to reflect on.
    if len(text) < MIN_RESPONSE_LENGTH:
        return False

    # Gate 2: Cooldown. We spoke recently.
    if is_on_cooldown():
        return False

    # Gate 3: Mostly code. The value is in reading it, not hearing about it.
    if code_ratio(text) > MAX_CODE_RATIO:
        return False

    # Gate 4: Random skip. Even if everything else passes,
    # sometimes just... don't. This prevents predictability.
    if random.random() < RANDOM_SKIP_CHANCE:
        return False

    return True


def main():
    # Read hook input
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Prevent infinite loops
    if hook_input.get('stop_hook_active', False):
        sys.exit(0)

    # Get transcript
    transcript_path = hook_input.get('transcript_path', '')
    if not transcript_path:
        sys.exit(0)

    # Extract response
    response_text = extract_last_response(transcript_path)
    if not response_text:
        sys.exit(0)

    # ── The Gates ──────────────────────────────────────────
    if not should_even_consider(response_text):
        sys.exit(0)

    # ── Past the gates — ask Haiku ────────────────────────
    # Haiku itself is another gate. It can (and often should) return SKIP.
    reflection = generate_reflection(response_text)
    if not reflection:
        sys.exit(0)

    # ── We have something worth saying ────────────────────
    record_spoke()
    asyncio.run(speak(reflection))
    sys.exit(0)


if __name__ == "__main__":
    main()
```

The gate cascade:

```
Response arrives
  │
  ├─ Too short? ──────────────── → silence  (most quick answers)
  ├─ On cooldown? ────────────── → silence  (spoke within 2 min)
  ├─ Mostly code? ────────────── → silence  (let them read)
  ├─ Random skip (30%)? ──────── → silence  (unpredictability)
  ├─ Haiku says SKIP? ────────── → silence  (nothing worth saying)
  │
  └─ All gates passed ────────── → speak    (~20-35% of responses)
```

---

## Step 6 — Hook Registration

**File: `hooks/hooks.json`**

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python \"<PLUGIN_PATH>/hooks/codetalk.py\"",
            "timeout": 30,
            "async": true
          }
        ]
      }
    ]
  }
}
```

`async: true` — the voice plays in the background. You can start typing your next prompt immediately. The reflection arrives a few seconds later, like a colleague who needed a moment to think.

> **After install:** replace `<PLUGIN_PATH>` with the actual plugin directory, e.g. `C:/Users/Ron/.claude/plugins/codetalk`

---

## Step 7 — Installation

### Option A: Local Marketplace (For Development)

```powershell
# Create marketplace wrapper
mkdir codetalk-marketplace\.claude-plugin -Force

@"
{
  "name": "codetalk-marketplace",
  "owner": { "name": "Ron" },
  "plugins": [
    {
      "name": "codetalk",
      "source": "./codetalk",
      "description": "Your code talks to you"
    }
  ]
}
"@ | Set-Content codetalk-marketplace\.claude-plugin\marketplace.json

# Place your plugin folder inside the marketplace dir
# Then in Claude Code:
#   /plugin marketplace add ./codetalk-marketplace
#   /plugin install codetalk@codetalk-marketplace
```

### Option B: Direct Hook (Quick Testing)

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python C:/Users/Ron/codetalk/hooks/codetalk.py",
            "timeout": 30,
            "async": true
          }
        ]
      }
    ]
  }
}
```

---

## Step 8 — Environment Variables

```powershell
# Required
[System.Environment]::SetEnvironmentVariable(
    "ANTHROPIC_API_KEY", "sk-ant-...", "User")

# Optional overrides
[System.Environment]::SetEnvironmentVariable(
    "CODETALK_VOICE", "en-US-GuyNeural", "User")
[System.Environment]::SetEnvironmentVariable(
    "CODETALK_RATE", "+5%", "User")
[System.Environment]::SetEnvironmentVariable(
    "CODETALK_PLAYER", "mpv", "User")
```

Restart terminal after setting.

---

## Step 9 — Testing

```powershell
# 1. Test TTS
edge-tts --voice en-US-GuyNeural --text "That connection pool change might bite you under high concurrency." --write-media test.mp3
mpv test.mp3

# 2. Test reflection generation (pass a realistic response)
python scripts/generate_reflection.py "I refactored the database module to use connection pooling with asyncpg instead of creating new connections per query. The pool is configured with min_size=5 and max_size=20, which should handle your current load. I also added a health check that pings the database every 30 seconds to keep connections alive and detect stale ones early. The retry logic wraps the entire transaction block so partial commits can't leak through."

# Expected: Either a genuine reflection OR "(silence)" on stderr

# 3. Test the full hook pipeline
echo '{"stop_hook_active": false, "transcript_path": "test-transcript.jsonl"}' | python hooks/codetalk.py

# 4. Use Claude Code normally — CodeTalk will speak occasionally
claude
```

---

## Tuning Guide

### Make It Speak More or Less

| Setting | More Voice | Less Voice |
|---------|-----------|------------|
| `MIN_RESPONSE_LENGTH` | Lower (200) | Higher (500) |
| `RANDOM_SKIP_CHANCE` | Lower (0.15) | Higher (0.50) |
| `COOLDOWN_SECONDS` | Lower (60) | Higher (300) |
| `MAX_CODE_RATIO` | Higher (0.85) | Lower (0.50) |
| System prompt | Softer SKIP criteria | Stricter SKIP criteria |

Start with the defaults. Live with them for a few days before adjusting. The temptation is to make it talk more — resist that.

### Voice Options

```powershell
edge-tts --list-voices   # See all available
```

| Voice | Character |
|-------|-----------|
| `en-US-GuyNeural` | Professional, calm male |
| `en-US-DavisNeural` | Relaxed, thoughtful male |
| `en-US-AriaNeural` | Conversational female |
| `en-US-JennyNeural` | Warm, friendly female |
| `en-GB-RyanNeural` | British male |

### Personality Variants

Edit `REFLECTION_SYSTEM_PROMPT` in `config.py`:

**The Spotter** (default) — catches what you might miss  
**The Strategist** — "Played it safe here. If you want speed over safety, you could..."  
**The Skeptic** — "This works, but I'd want to load test it before trusting those pool numbers."  
**The Minimalist** — cap at exactly one sentence, or SKIP

---

## Cost

| Component | Per Reflection |
|-----------|---------------|
| Haiku input (~400 tokens) | ~$0.0003 |
| Haiku output (~60 tokens) | ~$0.0002 |
| edge-tts | Free |
| **Total** | **~$0.0005** |

At ~15-20 reflections/day (given the gates): **~$0.01/day**, **~$0.25/month**.

---

## Known Considerations

1. **Transcript format**: The JSONL structure may vary across Claude Code versions. If extraction breaks, inspect the transcript file at the path shown in hook input and adjust `extract_last_response()`.

2. **Windows audio**: `mpv` is the most reliable. Install via `choco install mpv`. Falls back to PowerShell's MediaPlayer if needed.

3. **WSL**: If running Claude Code in WSL, audio needs PulseAudio routing to Windows. Simplest fix: install `mpv` on Windows natively and call via `cmd.exe /c mpv`.

4. **Cosmetic hook errors**: Some Claude Code versions show "Stop hook error" messages even when hooks work. This is a known issue — check GitHub if it appears.

5. **First run**: The first reflection takes slightly longer (~3-4s) because `edge-tts` downloads voice data. Subsequent runs are ~2s.

---

## Future Ideas

- **Toggle command**: `/codetalk on|off` to control mid-session
- **Context memory**: Feed previous reflections as context so commentary builds over a session
- **Hebrew mode**: edge-tts supports `he-IL-AvriNeural` — the prompt would need a Hebrew variant
- **Voice cloning**: Replace edge-tts with Coqui/Chatterbox for a unique voice
- **Adaptive frequency**: Track how often the user acts on reflections (e.g., immediately types a follow-up related to what was said) and adjust gate thresholds over time
