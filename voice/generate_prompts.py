"""
Fahamika — Generate Static Prompt Audio (run ONCE)
Generates the fixed voice prompts as WAV files via Sauti TTS.
These never change, so they're stored on disk and reused forever.

Run once on the VPS:
  python voice/generate_prompts.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.config import config
from voice.tts import synthesize

# Static prompts — spoken in Kiswahili by Sauti
PROMPTS = {
    "prompt_welcome": (
        "Karibu Fahamika. Tafadhali uliza swali lako kuhusu huduma za serikali, "
        "haki, au taarifa za kiserikali baada ya beep. Bonyeza hash ukimaliza."
    ),
    "prompt_ask_again": (
        "Tafadhali uliza swali lako baada ya beep. Bonyeza hash ukimaliza."
    ),
    "prompt_error_no_audio": (
        "Samahani, hatukuweza kupokea sauti yako. Tafadhali jaribu tena."
    ),
    "prompt_error_technical": (
        "Samahani, kuna tatizo la kiufundi. Tafadhali jaribu tena baadaye."
    ),
}


def main():
    config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Fahamika — Generating static prompt audio (Sauti TTS)")
    print("=" * 60)

    for name, text in PROMPTS.items():
        output_path = str(config.AUDIO_DIR / f"{name}.wav")
        synthesize(text, output_path=output_path)
        print(f"  ✓ {name}.wav ({len(text)} chars)")

    print("\nDone. Files saved to:", config.AUDIO_DIR)
    print("The server will serve them at /voice/audio/<name>.wav")


if __name__ == "__main__":
    main()
