# CodeTalk — Changelog

## [2026-02-26 16:10 ET] — Initial build from design doc

### Done
- Created full plugin structure under `codetalk/`
- `.claude-plugin/plugin.json` — plugin manifest (v1.0.0)
- `scripts/config.py` — all settings: LLM, TTS, gatekeeper, audio, reflection prompt
- `scripts/generate_reflection.py` — Haiku reflection call with SKIP support
- `scripts/speak.py` — edge-tts with mpv/ffplay/powershell playback
- `hooks/codetalk.py` — main gatekeeper with 5-gate cascade
- `hooks/hooks.json` — Stop hook registration (async, 30s timeout)
- `CLAUDE.md` — project-specific instructions and rules
- `CHANGELOG.md` — this file

### State
- All source files written and tested end-to-end
- Hook registered in `~/.claude/settings.json`
- `ANTHROPIC_API_KEY` set as persistent User env var (requires terminal restart)

### Next
- Restart terminal for env var to take effect
- Live test with Claude Code in a real session
- Monitor activation rate over a few days, tune gates if needed
- Consider installing `mpv` (`choco install mpv`) for better audio playback

### Files Changed
- `codetalk/.claude-plugin/plugin.json` (new)
- `codetalk/scripts/config.py` (new)
- `codetalk/scripts/generate_reflection.py` (new)
- `codetalk/scripts/speak.py` (new)
- `codetalk/hooks/codetalk.py` (new)
- `codetalk/hooks/hooks.json` (new)
- `CLAUDE.md` (new)
- `CHANGELOG.md` (new)
- `~/.claude/settings.json` (modified — added Stop hook)

## [2026-02-26 18:20 ET] — v2.0: Embedded reflections, Haiku removed

### Done
- **Architecture change:** Replaced Haiku LLM call with embedded reflections from main model (Opus)
  - Model now includes reflections directly in responses using `---\n> *text*\n` format
  - Hook extracts via regex instead of calling Haiku API
  - Reflections visible on screen AND spoken aloud
- **Voice upgrade:** Changed default from `en-US-GuyNeural` to `en-US-AndrewMultilingualNeural` (much more natural)
- **Transcript parser fix:** Was reading `entry.role`/`entry.content` (wrong); fixed to `entry.type`/`entry.message.content`
- **Multi-block fix:** Transcript entries are per-block (text, tool_use, thinking separately); now collects last 5 text blocks and matches the last reflection
- **Cleanup:**
  - Deleted `generate_reflection.py` (Haiku caller — no longer needed)
  - Stripped `config.py` to only TTS, audio, and cooldown settings
  - Removed `CODETALK_API_KEY` from User-level environment variables
  - Removed `anthropic` SDK dependency
  - Removed `.claude-plugin/` directory reference from docs
- **Added debug logging** to hook (`~/.claude/codetalk-debug.log`)
- **Updated CLAUDE.md** with reflection instructions, v2.0 status, new project structure
- **Updated MEMORY.md** with architecture notes and transcript format lessons

### State
- CodeTalk v2.0 live and E2E tested
- No API keys required
- Hook: extracts embedded reflection → edge-tts → PowerShell MediaPlayer
- Voice: `en-US-AndrewMultilingualNeural`
- Debug logging enabled

### Next
- Monitor activation rate over a few sessions
- Tune cooldown (currently 120s) based on feel
- Consider `choco install mpv` for faster audio playback
- Optionally remove debug logging once stable

### Files Changed
- `codetalk/hooks/codetalk.py` (rewritten — embedded extraction, debug logging)
- `codetalk/scripts/config.py` (stripped — Haiku/gate settings removed)
- `codetalk/scripts/generate_reflection.py` (deleted)
- `CLAUDE.md` (updated — v2.0, reflection instructions, new structure)
- `CHANGELOG.md` (this entry)

---

## [2026-02-26 16:25 ET] — Dependency install, testing, prompt tuning

### Done
- Installed `edge-tts` + `anthropic` on Python 3.14 (active Python, pip was linked to 3.12)
- Verified TTS playback works with PowerShell MediaPlayer (no mpv/ffplay installed)
- Verified Haiku API calls work (key validated)
- Discovered original SKIP-heavy system prompt caused Haiku to SKIP 100% of the time
  - Root cause: 5x SKIP mentions in system prompt + "or SKIP" in user message = too much pressure
  - Fix: reduced to single SKIP instruction in system prompt, simplified user message
- Full pipeline test successful: Haiku generated reflection about CDN+GraphQL gotcha, TTS spoke it
- Changed default `AUDIO_PLAYER` from `mpv` to `powershell` (no mpv installed)
- Set `ANTHROPIC_API_KEY` as persistent User env var
- Registered Stop hook in `~/.claude/settings.json`

### State
- CodeTalk fully operational, pending terminal restart for env var

### Files Changed
- `codetalk/scripts/config.py` (modified — tuned prompt, default player)
- `codetalk/scripts/generate_reflection.py` (modified — simplified user message)
- `~/.claude/settings.json` (modified — added Stop hook)
