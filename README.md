# CodeTalk

A spoken reflection layer for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI. CodeTalk gives Claude a voice — it speaks brief observations, task announcements, and non-obvious insights aloud while you work.

## How It Works

Claude embeds short spoken lines directly in its responses using a distinct format. A Stop hook extracts the text and plays it through your speakers via [edge-tts](https://github.com/rany2/edge-tts) (Microsoft's free neural TTS).

```
Your normal response text here...

---
> *This is what gets spoken aloud — a brief observation the model decided was worth saying.*
```

No second LLM call. No API key. The main model decides when to speak and what to say.

## Voice Behaviors

| Type | When | Example |
|------|------|---------|
| **Task start** | Beginning a non-trivial task | *"Refactoring the scanner to use connection pooling."* |
| **Task complete** | Finishing a task or milestone | *"Migration done, both tables updated."* |
| **Reflection** | ~30% of substantive responses | *"Removing that API key also eliminates the Sonnet charge risk."* |

Silence is the default. Not every response gets a spoken line.

## Setup

### 1. Install edge-tts

```bash
pip install edge-tts
```

### 2. Add the hook to Claude Code

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
            "command": "python \"/path/to/CodeTalk/codetalk/hooks/codetalk.py\"",
            "timeout": 30000
          }
        ]
      }
    ]
  }
}
```

### 3. Add voice instructions to your project

Copy the `## Voice Instructions (ACTIVE)` section from this project's `CLAUDE.md` into your own project's `CLAUDE.md`. This tells Claude when and how to embed spoken lines.

## Configuration

All settings are optional environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CODETALK_VOICE` | `en-US-AndrewMultilingualNeural` | edge-tts voice name |
| `CODETALK_RATE` | `+5%` | Speech rate adjustment |
| `CODETALK_PLAYER` | `powershell` | Audio player (`mpv`, `ffplay`, or `powershell`) |

### Changing the voice

```bash
# List all available voices
edge-tts --list-voices

# Good options for natural speech:
# en-US-AndrewMultilingualNeural (default, very natural)
# en-US-BrianMultilingualNeural (slightly deeper)
# en-GB-RyanNeural (British accent)
```

## Architecture

```
Claude Code response
    ↓
Stop hook fires → codetalk.py
    ↓
Extract "---\n> *text*" from last text block
    ↓
edge-tts → mp3 → audio playback
```

Three files, no API keys, no external LLM calls:

```
codetalk/
├── hooks/
│   └── codetalk.py    # Stop hook — extracts and speaks
└── scripts/
    ├── config.py      # Voice, rate, player settings
    └── speak.py       # edge-tts + audio playback
```

## Debug

Check `~/.claude/codetalk-debug.log` to see what the hook is doing:

```
15:38:02 Hook invoked
15:38:02 Found reflection: Removing that API key also eliminates the...
15:38:02 Speaking...
15:38:16 Done speaking
```

## Requirements

- Python 3.10+
- [edge-tts](https://github.com/rany2/edge-tts)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI with hooks support
- Windows (PowerShell MediaPlayer) or mpv/ffplay for audio playback

## License

MIT
