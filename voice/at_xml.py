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
    """Answer, play a prompt, then record the caller.

    Per AT docs, the <Say> prompt is NESTED INSIDE <Record> for partial
    recording (recording stops on # / maxLength and AT sends the URL
    mid-call). A sibling <Say> would be treated as a terminal recording.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Record
        finishOnKey="{finish_on_key}"
        maxLength="{max_length}"
        trimSilence="true"
        playBeep="true"
        callbackUrl="{recording_url_callback}"
    >
        <Say voice="{voice}" playBeep="false">{_escape(prompt)}</Say>
    </Record>
</Response>"""


def answer_play_and_record(
    prompt_audio_url: str,
    recording_url_callback: str,
    max_length: int = 30,
    finish_on_key: str = "#",
) -> str:
    """Answer, play a pre-recorded prompt via <Play>, then record the caller.

    The <Play> prompt is NESTED INSIDE <Record> for partial recording
    (stops on # / maxLength, AT sends URL mid-call).
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Record
        finishOnKey="{finish_on_key}"
        maxLength="{max_length}"
        trimSilence="true"
        playBeep="true"
        callbackUrl="{recording_url_callback}"
    >
        <Play url="{prompt_audio_url}"/>
    </Record>
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
    prompt: str = "Please ask your question after the beep. Press hash when done.",
    max_length: int = 30,
    finish_on_key: str = "#",
    voice: str = "woman",
) -> str:
    """Speak the answer, then prompt for another question and record.

    The answer is spoken as a sibling <Say> BEFORE the record block;
    the "press #" prompt is NESTED INSIDE <Record> (AT partial recording).
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}" playBeep="false">{_escape(answer)}</Say>
    <Record
        finishOnKey="{finish_on_key}"
        maxLength="{max_length}"
        trimSilence="true"
        playBeep="true"
        callbackUrl="{recording_url_callback}"
    >
        <Say voice="{voice}" playBeep="false">{_escape(prompt)}</Say>
    </Record>
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
    prompt_audio_url: str,
    max_length: int = 30,
    finish_on_key: str = "#",
) -> str:
    """Play a TTS audio answer, then play a pre-recorded prompt, then record.

    The answer is a sibling <Play> BEFORE the record block; the prompt is
    NESTED INSIDE <Record> (AT partial recording).
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play url="{audio_url}"/>
    <Record
        finishOnKey="{finish_on_key}"
        maxLength="{max_length}"
        trimSilence="true"
        playBeep="true"
        callbackUrl="{recording_url_callback}"
    >
        <Play url="{prompt_audio_url}"/>
    </Record>
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
