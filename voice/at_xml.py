"""
Fahamika Voice Pipeline — Africa's Talking VoiceXML Builder
Constructs XML responses for AT's Voice API call control.

AT Voice API reference: https://developers.africastalking.com/docs/voice/overview
"""

from typing import Optional


def answer_say(text: str, voice: str = "woman") -> str:
    """Answer the call and speak a message."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}" playBeep="false">{_escape(text)}</Say>
</Response>"""


def answer_say_and_record(
    prompt: str,
    recording_url_callback: str,
    max_length: int = 30,
    finish_on_key: str = "#",
    voice: str = "woman",
) -> str:
    """Answer, play a prompt, then record the caller."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}" playBeep="false">{_escape(prompt)}</Say>
    <Record
        finishOnKey="{finish_on_key}"
        maxLength="{max_length}"
        trimSilence="true"
        playBeep="true"
        callbackUrl="{recording_url_callback}"
    />
</Response>"""


def say_and_hangup(text: str, voice: str = "woman") -> str:
    """Speak a message and hang up."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}" playBeep="false">{_escape(text)}</Say>
    <Hangup/>
</Response>"""


def say_and_record_again(
    answer: str,
    recording_url_callback: str,
    prompt: str = "Press hash to ask another question, or simply hang up.",
    max_length: int = 30,
    finish_on_key: str = "#",
    voice: str = "woman",
) -> str:
    """Speak the answer, then prompt for another question and record."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}" playBeep="false">{_escape(answer)}</Say>
    <Say voice="{voice}" playBeep="false">{_escape(prompt)}</Say>
    <Record
        finishOnKey="{finish_on_key}"
        maxLength="{max_length}"
        trimSilence="true"
        playBeep="true"
        callbackUrl="{recording_url_callback}"
    />
</Response>"""


def say_and_redirect(text: str, redirect_url: str, voice: str = "woman") -> str:
    """Speak a message, then redirect to another callback."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}" playBeep="false">{_escape(text)}</Say>
    <Redirect>{_escape(redirect_url)}</Redirect>
</Response>"""


def play_and_hangup(audio_url: str) -> str:
    """Play an audio file URL and hang up. Used for error exits with custom TTS."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play url="{audio_url}"/>
    <Hangup/>
</Response>"""


def play_and_record_again(
    audio_url: str,
    recording_url_callback: str,
    prompt: str = "Press hash to ask another question, or simply hang up.",
    max_length: int = 30,
    finish_on_key: str = "#",
    voice: str = "woman",
) -> str:
    """Play a TTS audio answer, then prompt for another question and record."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play url="{audio_url}"/>
    <Say voice="{voice}" playBeep="false">{_escape(prompt)}</Say>
    <Record
        finishOnKey="{finish_on_key}"
        maxLength="{max_length}"
        trimSilence="true"
        playBeep="true"
        callbackUrl="{recording_url_callback}"
    />
</Response>"""


def reject(reason: str = "busy") -> str:
    """Reject the incoming call."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Reject reason="{reason}"/>
</Response>"""


def _escape(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
