"""Voice input — speak a question instead of typing it.

Uses Streamlit's native `st.audio_input` to record in the browser, then
OpenAI's transcription API to turn it into text.

The one non-obvious piece is the vocabulary prompt. Speech models are trained
mostly on ordinary speech, so spoken code terms come back mangled —
"useEffect" becomes "use effect", "async" becomes "a sync", "TypeScript"
becomes "type script". The transcription endpoint accepts a `prompt` that
biases decoding toward expected vocabulary, so we hand it a list of common
programming terms. That single parameter is the difference between a usable
coding transcript and a frustrating one.
"""

from __future__ import annotations

import hashlib

TRANSCRIBE_MODEL = "whisper-1"

# Biases the decoder toward technical vocabulary. Kept short on purpose —
# the API only reads roughly the first 224 tokens of this.
CODING_VOCAB_PROMPT = (
    "The speaker is a software developer asking a coding question. Expect terms "
    "like: JavaScript, TypeScript, Python, React, useState, useEffect, useMemo, "
    "async, await, Promise, API, JSON, SQL, query, function, const, let, array, "
    "object, class, method, npm, pip, git, commit, merge, Docker, Kubernetes, "
    "Node.js, Next.js, Tailwind, Django, Flask, FastAPI, endpoint, middleware, "
    "component, props, state, hook, refactor, debug, stack trace, null, "
    "undefined, boolean, integer, string, TypeError, syntax error, for loop, "
    "recursion, algorithm, big O, database, schema, migration, deployment."
)


def audio_fingerprint(audio_bytes: bytes) -> str:
    """Stable id for a recording, so we transcribe each clip exactly once.

    Streamlit reruns the whole script constantly and the recorded clip stays
    sitting in the widget, so without this the same audio would be sent (and
    billed) on every rerun.
    """
    return hashlib.sha256(audio_bytes).hexdigest()[:16]


def transcribe(audio_bytes: bytes, api_key: str, filename: str = "speech.wav") -> str:
    """Return the spoken text. Raises with a readable message on failure."""
    if not audio_bytes:
        raise ValueError("The recording was empty — try holding the mic a moment longer.")
    if not api_key:
        raise ValueError("Add your OpenAI API key in the sidebar to use voice input.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    result = client.audio.transcriptions.create(
        model=TRANSCRIBE_MODEL,
        file=(filename, audio_bytes),
        prompt=CODING_VOCAB_PROMPT,
    )
    return (result.text or "").strip()
