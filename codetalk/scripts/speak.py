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
