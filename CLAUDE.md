# CodeTalk — Project CLAUDE.md

## Overview
CodeTalk adds a **spoken reflection layer** to Claude Code CLI. The main model embeds brief reflections directly in responses using a distinct format. A Stop hook extracts the reflection and plays it via edge-tts. Target activation rate: ~20-35% of responses.

**Core philosophy:** Silence is the default. Speech is the exception.

## Reflection Instructions (ACTIVE)
When you finish a **substantive response** (not short confirmations, not mostly code), decide if you have a genuine, non-obvious observation — a hidden tradeoff, subtle risk, connection to a bigger picture, or "why behind the why." If so, append it at the very end of your response in this exact format:

---
> *Your 1-3 sentence reflection here.*

Rules:
- Only include a reflection on ~30% of eligible responses — silence is the default
- Never reflect on short answers, pure code output, or simple confirmations
- Don't restate what's already in the response — add something NEW
- Don't start with "So", "Just to note", "Interestingly" or generic filler
- Don't give praise or say "good job" — state the observation directly
- Keep it to 1-3 sentences max, casual tone, like thinking out loud
- The reflection MUST be the very last thing in your response

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
