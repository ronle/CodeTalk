#!/usr/bin/env python3
"""
CodeTalk — Stop hook for Claude Code.

Extracts embedded reflections from Claude's responses and speaks them.
The model decides when to reflect — this hook just extracts and speaks.
"""
import json
import sys
import os
import re
import time
import asyncio

# Add scripts dir to path
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', 'scripts')
sys.path.insert(0, SCRIPT_DIR)

from config import COOLDOWN_SECONDS, COOLDOWN_FILE
from speak import speak

# Reflection format: ---\n> *reflection text*\n
REFLECTION_PATTERN = re.compile(
    r'---\s*\n>\s*\*(.+?)\*\s*$',
    re.DOTALL
)


def log_debug(msg: str):
    """Append debug info to a log file."""
    log_path = os.path.join(
        os.path.expanduser("~"), ".claude", "codetalk-debug.log"
    )
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except OSError:
        pass


def extract_reflection(transcript_path: str) -> str | None:
    """Find an embedded reflection in the last assistant text blocks."""
    if not os.path.exists(transcript_path):
        return None

    # Collect all assistant text blocks from the transcript
    all_assistant_text = []

    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                msg = entry.get('message', entry)
                entry_type = entry.get('type', msg.get('role', ''))
                if entry_type == 'assistant':
                    content = msg.get('content', [])
                    for block in content:
                        if isinstance(block, dict) and \
                                block.get('type') == 'text':
                            text = block.get('text', '')
                            if text:
                                all_assistant_text.append(text)
            except json.JSONDecodeError:
                continue

    if not all_assistant_text:
        return None

    # Check the last few text blocks for the reflection pattern
    # (reflection is always at the end of the response)
    # Use findall to get the LAST match (most recent reflection)
    combined = '\n'.join(all_assistant_text[-5:])
    matches = REFLECTION_PATTERN.findall(combined)

    if matches:
        return matches[-1].strip()

    return None


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


def main():
    log_debug("Hook invoked")

    # Read hook input
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        log_debug("Failed to read stdin")
        sys.exit(0)

    # Prevent infinite loops
    if hook_input.get('stop_hook_active', False):
        log_debug("Exiting: stop_hook_active")
        sys.exit(0)

    # Get transcript
    transcript_path = hook_input.get('transcript_path', '')
    if not transcript_path:
        log_debug("Exiting: no transcript_path")
        sys.exit(0)

    # Extract embedded reflection
    reflection = extract_reflection(transcript_path)
    if not reflection:
        log_debug("Exiting: no reflection found")
        sys.exit(0)
    log_debug(f"Found reflection: {reflection[:80]}...")

    # Cooldown check
    if is_on_cooldown():
        log_debug("Exiting: on cooldown")
        sys.exit(0)

    # Speak it
    log_debug("Speaking...")
    record_spoke()
    try:
        asyncio.run(speak(reflection))
        log_debug("Done speaking")
    except Exception as e:
        log_debug(f"Speak error: {e}")
    sys.exit(0)


if __name__ == "__main__":
    main()
