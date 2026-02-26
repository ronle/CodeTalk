#!/usr/bin/env python3
"""
CodeTalk — Stop hook for Claude Code.

Extracts embedded reflections from Claude's responses and speaks them.
The model decides when to speak — this hook just extracts and speaks.
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

    # Only check the LAST text block — reflection must be the final
    # thing in the response, so it'll be in the last text block.
    # Checking more blocks would re-speak old reflections.
    last_block = all_assistant_text[-1]
    match = REFLECTION_PATTERN.search(last_block)

    if match:
        return match.group(1).strip()

    return None


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

    # Speak it
    log_debug("Speaking...")
    try:
        asyncio.run(speak(reflection))
        log_debug("Done speaking")
    except Exception as e:
        log_debug(f"Speak error: {e}")
    sys.exit(0)


if __name__ == "__main__":
    main()
