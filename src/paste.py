"""A paste-to-attach zone for screenshots.

Streamlit's `st.file_uploader` cannot accept a clipboard paste — the browser
only fires a `paste` event at focused DOM, and the uploader doesn't listen for
one. So this is a tiny custom component: a single HTML file that listens for
the paste, reads the image out of the clipboard, and hands the data URL back to
Python through Streamlit's component message protocol.

No npm build and no third-party package — `declare_component(path=...)` will
serve a plain folder, and the protocol is three `postMessage` calls, which the
HTML implements directly.
"""

from __future__ import annotations

import base64
import os

import streamlit.components.v1 as components

_BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paste_zone")

_paste_zone = components.declare_component("codesage_paste_zone", path=_BUILD_DIR)


def paste_zone(key: str = "paste_zone") -> dict | None:
    """Render the paste target. Returns {'data_url', 'bytes', 'ts'} or None."""
    return _paste_zone(key=key, default=None)


def decode_data_url(data_url: str) -> tuple[bytes, str]:
    """Split a data URL into raw bytes and its mime type."""
    header, _, encoded = data_url.partition(",")
    mime = "image/png"
    if header.startswith("data:") and ";" in header:
        mime = header[5 : header.index(";")] or mime
    return base64.b64decode(encoded), mime


# ---------------------------------------------------------------------------
# Back-to-top button
#
# Streamlit scrolls an inner container, not the window, so an anchor link does
# nothing. This tiny component reaches the host page (same origin) and scrolls
# that container instead.
# ---------------------------------------------------------------------------
_SCROLL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scroll_top")
_scroll_top = components.declare_component("codesage_scroll_top", path=_SCROLL_DIR)


def scroll_top_button(key: str = "scroll_top") -> None:
    """Render a 'back to top' button that works with Streamlit's scroller."""
    _scroll_top(key=key, default=None)
