# CodeTalk — Project CLAUDE.md

## Overview
CodeTalk adds a **spoken reflection layer** to Claude Code CLI. The main model embeds brief reflections directly in responses using a distinct format. A Stop hook extracts the reflection and plays it via edge-tts. Target activation rate: ~20-35% of responses.

**Core philosophy:** Silence is the default. Speech is the exception.

## Voice Instructions (ACTIVE)
Append a spoken line at the very end of your response using this exact format:

---
> *Your spoken line here.*

There are three types of spoken lines:

### 1. Task start
When you begin working on a non-trivial task (multi-step, multi-file, or requires investigation), announce what you're about to do in one short sentence. Keep it direct — e.g. "Refactoring the scanner to use connection pooling." or "Digging into why the hook isn't firing."

### 2. Task complete
When you finish a task or reach a clear milestone, announce it in one short sentence. e.g. "Database migration is done, both tables updated." or "All tests passing now."

### 3. Reflection
On ~30% of substantive responses, include a genuine non-obvious observation — a hidden tradeoff, subtle risk, connection to a bigger picture, or "why behind the why."

### Rules
- The spoken line MUST be the very last thing in your response
- Keep it to 1-2 sentences max, casual tone, like thinking out loud
- Don't start with "So", "Just to note", "Interestingly" or generic filler
- Don't give praise — state observations directly
- Don't restate what's already in the response — add something NEW
- Never speak on short answers, pure code output, or simple confirmations
- Task start/complete announcements take priority over reflections
- Silence is still the default — not every response needs a spoken line

## Current Status
- **Version:** 2.0.0
- **State:** Live — embedded reflections, no Haiku, E2E tested
- **Last Updated:** 2026-02-26

## Project Structure
```
CodeTalk/
├── codetalk-plugin-instructions.md   # Original design doc (historical)
├── CLAUDE.md                         # This file (includes reflection instructions)
├── CHANGELOG.md                      # Session log
└── codetalk/                         # Plugin root
    ├── hooks/
    │   └── codetalk.py               # Stop hook — extracts reflection + speaks
    └── scripts/
        ├── config.py                 # TTS, audio, cooldown settings
        └── speak.py                  # edge-tts + audio playback
```

## Dependencies
| Package | Purpose | Install |
|---------|---------|---------|
| `edge-tts` | Free neural TTS | `pip install edge-tts` |

## Environment Variables
| Variable | Required | Default |
|----------|----------|---------|
| `CODETALK_VOICE` | No | `en-US-AndrewMultilingualNeural` |
| `CODETALK_RATE` | No | `+5%` |
| `CODETALK_PLAYER` | No | `powershell` |

## Key Design Decisions
- **Embedded reflections** — main model generates reflections inline, no second LLM call
- **2-minute cooldown** between reflections — no rapid-fire
- **~30% activation** on eligible responses — model self-regulates via CLAUDE.md instructions
- **Visible on screen** — reflection text is displayed in distinct format (blockquote italic) so user can read what was spoken
- **Hook registered** in `~/.claude/settings.json` (Stop hook, 30s timeout)

## Lessons Learned
- **Transcript format:** Claude Code transcript JSONL uses `entry.message.content` not `entry.content`. Each content block is a separate JSONL entry (text, tool_use, thinking).
- **Voice choice:** `en-US-AndrewMultilingualNeural` is significantly more natural than default `en-US-GuyNeural`.
- **Python version mismatch:** `pip` targets 3.12, `python` targets 3.14. Always use `python -m pip install`.

## Safety Rules
- **2-minute cooldown** minimum between spoken reflections
- Reflections must be the LAST thing in the response (hook extracts from end)
- Do NOT reflect on every response — silence is the default

## Testing
```powershell
# 1. Test TTS alone
edge-tts --voice en-US-AndrewMultilingualNeural --text "Testing voice" --write-media test.mp3

# 2. Test full hook pipeline (after a response with embedded reflection)
# Check: ~/.claude/codetalk-debug.log
```

## Installation
Add to `~/.claude/settings.json` under `hooks.Stop`, or use the plugin marketplace approach. See `codetalk-plugin-instructions.md` for full details.
