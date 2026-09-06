"""CodeSage AI — a coding-only chat assistant built with LangChain + Streamlit.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src.cache_manager import CACHE_CHOICES, configure_cache
from src.chains import (
    CHAIN_SOURCE,
    build_llm,
    stream_answer,
    to_langchain_history,
)
from src.config import (
    APP_ICON,
    APP_NAME,
    APP_TAGLINE,
    CUSTOM_MODEL_LABEL,
    CUSTOM_ROLE_LABEL,
    NO_ROLE_LABEL,
    ROLE_PRESETS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DISCLAIMER,
    LANGUAGE_HINTS,
    LANGUAGES,
    MODEL_GUIDE,
    MODEL_OPTIONS,
    MODEL_WARNING_PREFIXES,
    MODES,
    REVIEW_MODES,
    OPENAI_API_KEY,
    STARTER_PROMPTS,
    MAX_IMAGES,
    MAX_IMAGE_MB,
    is_valid_key,
    model_help,
    supports_temperature,
    supports_vision,
)
from src.guard import is_coding_request
from src.prompts import (
    build_code_block,
    build_language_instruction,
    build_mode_instruction,
    build_role_instruction,
    refusal_message,
    role_rejection_message,
)
from src.paste import decode_data_url, paste_zone, scroll_top_button
from src.roles import suggest_alternative, validate_role
from src.styles import SCENERY_CSS, hero_html, label
from src.tech_notes import TECH_NOTES, build_tech_context, detect_stacks
from src.utils import count_lines, detect_language, looks_like_code
from src.voice import audio_fingerprint, transcribe

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{APP_NAME} — Smart Coding Assistant",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(SCENERY_CSS, unsafe_allow_html=True)

DEFAULTS = {
    "messages": [],          # [{role, content}]
    "pending": None,         # question queued from a starter chip
    "code": "",
    "answers": 0,
    "redirects": 0,
    "role_checks": {},       # {role text: (accepted, reason)} — avoids re-billing
    "voice_draft": "",       # transcript waiting to be reviewed and sent
    "last_voice": None,      # fingerprint of the clip already transcribed
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


# ---------------------------------------------------------------------------
# Sidebar — keys, model, behaviour
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.caption(APP_TAGLINE)

    st.divider()
    st.markdown("### 🔑 OpenAI API key")
    typed_key = st.text_input(
        "Your key",
        type="password",
        placeholder="sk-…",
        key="api_key_input",
        help="Used only for this session and never stored. Get one at platform.openai.com.",
        label_visibility="collapsed",
    )

    if typed_key:
        if is_valid_key(typed_key):
            active_api_key = typed_key
            key_ready = True
            st.success("Key accepted for this session.", icon="✅")
        else:
            active_api_key = ""
            key_ready = False
            st.error("That doesn't look like an OpenAI key (should start with `sk-`).", icon="⚠️")
    elif OPENAI_API_KEY:
        active_api_key = OPENAI_API_KEY
        key_ready = True
        st.info("Using the key from the app's environment.", icon="🗝️")
    else:
        active_api_key = ""
        key_ready = False
        st.warning("Paste your OpenAI key above to start chatting.", icon="🔐")

    st.divider()
    st.markdown("### 🤖 Model")
    model_choice = st.selectbox(
        "Model",
        list(MODEL_OPTIONS.keys()) + [CUSTOM_MODEL_LABEL],
        index=list(MODEL_OPTIONS.keys()).index(DEFAULT_MODEL)
        if DEFAULT_MODEL in MODEL_OPTIONS
        else 0,
        label_visibility="collapsed",
    )
    if model_choice == CUSTOM_MODEL_LABEL:
        model_name = st.text_input("Custom model id", value=DEFAULT_MODEL).strip()
    else:
        model_name = model_choice
    st.caption(model_help(model_name))

    with st.expander("🧭 Which model should I pick?"):
        st.markdown(
            "\n".join(
                f"**{task}** → `{model}`  \n<span style='opacity:.7;font-size:.85em'>{why}</span>"
                for task, model, why in MODEL_GUIDE
            ),
            unsafe_allow_html=True,
        )
        st.caption(
            "Rule of thumb: the cheap models are fine when nothing gets changed "
            "(explaining, learning). Anything that edits or judges your code "
            "deserves gpt-4o or better — a weak model invents bugs that aren't there."
        )

    if supports_temperature(model_name):
        temperature = st.slider(
            "Creativity",
            0.0, 1.0, DEFAULT_TEMPERATURE, 0.05,
            help="Low keeps answers precise and repeatable — best for code.",
        )
    else:
        temperature = DEFAULT_TEMPERATURE
        st.caption("This model uses a fixed temperature.")

    st.divider()
    st.markdown("### 🗄️ Caching")
    cache_choice = st.radio(
        "Cache",
        CACHE_CHOICES,
        index=0,
        label_visibility="collapsed",
        help="Repeating an identical question returns instantly and costs nothing.",
    )
    cache_status = configure_cache(cache_choice)
    st.caption(cache_status)

    st.divider()
    st.markdown("### 📊 This session")
    col_a, col_b = st.columns(2)
    col_a.metric("Answers", st.session_state.answers)
    col_b.metric("Redirects", st.session_state.redirects)

    if st.button("🧹 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.answers = 0
        st.session_state.redirects = 0
        st.session_state.pending = None
        st.rerun()

    st.divider()
    st.caption(f"Role: {st.session_state.get('active_role') or 'none assigned'}")
    st.caption(f"Chain: `{CHAIN_SOURCE}`")
    st.caption(DISCLAIMER)


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(hero_html(APP_ICON, APP_NAME, APP_TAGLINE), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Role assignment — tech roles only
# ---------------------------------------------------------------------------
def check_role(role_text: str):
    """Validate a role, remembering the verdict so we don't pay for it twice."""
    cached = st.session_state.role_checks.get(role_text)
    if cached is not None:
        return cached

    checker = None
    if key_ready:
        checker = build_llm(
            model_name="gpt-4o-mini",
            temperature=0.0,
            streaming=False,
            api_key=active_api_key,
        )
    verdict = validate_role(role_text, checker)
    st.session_state.role_checks[role_text] = verdict
    return verdict


role_left, role_right = st.columns([1, 1])

# Presets minus the two control entries — the multiselect needs real roles only.
SELECTABLE_ROLES = [
    r for r in ROLE_PRESETS if r not in (NO_ROLE_LABEL, CUSTOM_ROLE_LABEL)
]

with role_left:
    st.markdown(label("Assign role(s) — pick as many as fit"), unsafe_allow_html=True)
    role_choices = st.multiselect(
        "Roles",
        SELECTABLE_ROLES,
        label_visibility="collapsed",
        placeholder="No specific role",
        help="Combine roles — e.g. MERN developer + Security engineer.",
    )

with role_right:
    st.markdown(label("Custom roles (tech only, comma-separated)"), unsafe_allow_html=True)
    custom_role = st.text_input(
        "Custom role",
        placeholder="e.g. Senior Rust systems engineer, SRE",
        label_visibility="collapsed",
        help="Any technology role. Non-coding roles are declined.",
    )

# Resolve the active role set: presets first, then any custom ones that pass
# the tech-only check.
personas: list[str] = [ROLE_PRESETS[r] for r in role_choices]
accepted_labels: list[str] = list(role_choices)
blocked_roles: list[str] = []

for raw in custom_role.split(","):
    typed_role = raw.strip()
    if not typed_role:
        continue
    accepted, _reason = check_role(typed_role)
    if accepted:
        personas.append(f"a {typed_role}")
        accepted_labels.append(typed_role)
    else:
        blocked_roles.append(typed_role)

for blocked in blocked_roles:
    st.warning(
        role_rejection_message(blocked, suggest_alternative(blocked)),
        icon="🚫",
    )

if accepted_labels:
    st.success(
        "Answering as **" + "** + **".join(accepted_labels) + "**.",
        icon="🎭",
    )

role_instruction = build_role_instruction(personas)
role_label = " + ".join(accepted_labels)
st.session_state.active_role = role_label or ""


# ---------------------------------------------------------------------------
# Mode + language controls
# ---------------------------------------------------------------------------
ctrl_left, ctrl_right = st.columns([3, 1])

with ctrl_left:
    st.markdown(label("What should CodeSage do?"), unsafe_allow_html=True)
    mode = st.radio(
        "Mode",
        list(MODES.keys()),
        horizontal=True,
        label_visibility="collapsed",
        format_func=lambda m: f"{MODES[m]['icon']} {m}",
    )
    st.caption(MODES[mode]["blurb"])

    # A weak model on a judging task is the main cause of invented "bugs".
    if mode in REVIEW_MODES and model_name.startswith(MODEL_WARNING_PREFIXES):
        st.warning(
            f"**{mode}** with `{model_name}` is a risky combination — small models "
            "tend to invent problems in working code. Switch to **gpt-4o** in the "
            "sidebar for anything that judges or edits your code.",
            icon="🎯",
        )

with ctrl_right:
    st.markdown(label("Language"), unsafe_allow_html=True)
    language = st.selectbox(
        "Language", LANGUAGES, label_visibility="collapsed"
    )

    st.markdown(label("Target stack / versions"), unsafe_allow_html=True)
    stack_hint = st.text_input(
        "Stack",
        placeholder="e.g. React 19, Next.js 15, Tailwind v4",
        label_visibility="collapsed",
        help=(
            "Pin the versions you're on. CodeSage writes for these instead of "
            "defaulting to the older versions that dominate training data."
        ),
    )


# ---------------------------------------------------------------------------
# Optional code panel
# ---------------------------------------------------------------------------
code_lines = count_lines(st.session_state.get("code_area", ""))
panel_title = (
    f"📋 Your code — {code_lines} line{'s' if code_lines != 1 else ''} pasted"
    if code_lines
    else "📋 Paste code here (optional)"
)

with st.expander(panel_title, expanded=not st.session_state.messages):
    code_input = st.text_area(
        "Code",
        height=220,
        key="code_area",
        placeholder="Paste the code you want reviewed, explained, fixed or optimised…",
        label_visibility="collapsed",
    )
    if code_input.strip():
        guessed = detect_language(code_input)
        meta = f"{count_lines(code_input)} lines"
        if guessed:
            meta += f" · looks like **{guessed}**"
        st.caption(meta)

    st.markdown(label("…or paste a screenshot"), unsafe_allow_html=True)
    pasted = paste_zone()

    st.markdown(label("…or browse for a file"), unsafe_allow_html=True)
    uploads = st.file_uploader(
        "Screenshots",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help=(
            "Screenshot of code, an error dialog or a terminal trace. "
            "Needs a vision-capable model (gpt-4o and newer)."
        ),
    )

code_input = st.session_state.get("code_area", "")

# --- Screenshots (pasted or uploaded) ---------------------------------------
images: list[dict] = []
has_attachments = bool(uploads) or bool(pasted)

if has_attachments:
    vision_ok = supports_vision(model_name)
    if not vision_ok:
        st.warning(
            f"`{model_name}` can't read images. Switch to **gpt-4o**, **gpt-4.1** "
            "or **gpt-5** in the sidebar, or remove the screenshots.",
            icon="👁️",
        )
    else:
        # A pasted screenshot goes first — it's the one just acted on.
        if pasted and pasted.get("data_url"):
            try:
                raw, mime = decode_data_url(pasted["data_url"])
                images.append({"bytes": raw, "mime": mime, "source": "pasted"})
            except Exception:
                st.warning("That clipboard image couldn't be read.", icon="📋")

        for upload in (uploads or [])[:MAX_IMAGES]:
            data = upload.getvalue()
            size_mb = len(data) / (1024 * 1024)
            if size_mb > MAX_IMAGE_MB:
                st.warning(
                    f"`{upload.name}` is {size_mb:.1f} MB — over the "
                    f"{MAX_IMAGE_MB} MB limit, so it was skipped.",
                    icon="📦",
                )
                continue
            images.append({"bytes": data, "mime": upload.type or "image/png"})
            if len(images) >= MAX_IMAGES:
                break

        if len(uploads) > MAX_IMAGES:
            st.caption(f"Only the first {MAX_IMAGES} screenshots are sent.")

        if images:
            st.caption(
                f"🖼️ {len(images)} screenshot{'s' if len(images) != 1 else ''} "
                "attached — CodeSage will read the code from the image."
            )
            # The paste zone shows its own thumbnail, so only preview uploads.
            file_previews = [img for img in images if img.get("source") != "pasted"]
            if file_previews:
                preview_cols = st.columns(len(file_previews))
                for col, img in zip(preview_cols, file_previews):
                    col.image(img["bytes"], use_container_width=True)

# Tell the user when version-specific notes are in play, so it's visible that
# the answer is being grounded rather than guessed from old training data.
detected_stacks = detect_stacks(stack_hint, code_input)
if detected_stacks:
    versions = ", ".join(TECH_NOTES[key]["current"] for key in detected_stacks)
    st.caption(f"📌 Current-version notes loaded for: **{versions}**")


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown(label("Try one of these"), unsafe_allow_html=True)
    starter_cols = st.columns(len(STARTER_PROMPTS))
    for col, prompt_text in zip(starter_cols, STARTER_PROMPTS):
        if col.button(prompt_text, use_container_width=True, key=f"starter_{prompt_text[:18]}"):
            st.session_state.pending = prompt_text
            st.rerun()

for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else APP_ICON
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------
# Once the chat is long, scrolling back to the settings is painful.
if len(st.session_state.messages) >= 2:
    top_col, _rest = st.columns([1, 4])
    with top_col:
        scroll_top_button()

# A bad answer (a repetition glitch, a cut-off reply) should cost one click,
# not retyping the whole question.
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    regen_col, _spacer = st.columns([1, 4])
    if regen_col.button("🔄 Regenerate", use_container_width=True,
                        help="Run the same question again"):
        last_user_idx = None
        for idx in range(len(st.session_state.messages) - 1, -1, -1):
            if st.session_state.messages[idx]["role"] == "user":
                last_user_idx = idx
                break
        if last_user_idx is not None:
            question_again = st.session_state.messages[last_user_idx]["content"]
            # Drop that question and its answer, then re-ask it.
            st.session_state.messages = st.session_state.messages[:last_user_idx]
            st.session_state.pending = question_again
            st.rerun()

# ---------------------------------------------------------------------------
# Voice input — sits directly above the chat bar so it stays reachable
# however long the conversation gets.
# ---------------------------------------------------------------------------
voice_col, voice_hint = st.columns([1, 4], vertical_alignment="center")

with voice_col:
    with st.popover("🎙️ Speak", use_container_width=True):
        st.caption("Record your question, then stop. You can edit it before sending.")
        clip = st.audio_input("Record", label_visibility="collapsed", key="voice_clip")

        with st.expander("Mic not working?"):
            st.markdown(
                "- **Allow the microphone.** Click the lock/🎙 icon in the address "
                "bar → Microphone → Allow, then reload.\n"
                "- **Use `localhost`.** Browsers only grant mic access on "
                "`localhost` or `https://`. A `192.168.x.x` address is blocked, "
                "which shows as *An error has occurred*.\n"
                "- **Check the device.** No microphone (or one in use by another "
                "app) fails the same way.\n"
                "- Or upload an audio file below instead."
            )
            audio_file = st.file_uploader(
                "Audio file",
                type=["wav", "mp3", "m4a", "webm", "ogg"],
                label_visibility="collapsed",
                key="voice_file",
            )
            if audio_file is not None:
                clip = audio_file

        if clip is not None:
            audio_bytes = clip.getvalue()
            fingerprint = audio_fingerprint(audio_bytes)
            # Transcribe each clip once — Streamlit reruns constantly and the
            # recording stays in the widget, so this avoids repeat billing.
            if fingerprint != st.session_state.last_voice:
                st.session_state.last_voice = fingerprint
                with st.spinner("Transcribing…"):
                    try:
                        st.session_state.voice_draft = transcribe(
                            audio_bytes, active_api_key,
                            filename=getattr(clip, "name", "speech.wav"),
                        )
                    except Exception as exc:
                        st.error(f"Couldn't transcribe that: {exc}", icon="🎤")

with voice_hint:
    if not st.session_state.voice_draft:
        st.caption("🎤 Prefer talking? Hit **Speak**, say your question, and edit it before it sends.")

# Review the transcript before it goes anywhere — speech models mishear code
# terms, so sending blind would waste a request.
if st.session_state.voice_draft:
    st.markdown(label("Heard you say — edit if needed"), unsafe_allow_html=True)
    edited = st.text_area(
        "Transcript",
        value=st.session_state.voice_draft,
        height=90,
        label_visibility="collapsed",
        key="voice_text",
    )
    send_col, clear_col, _ = st.columns([1, 1, 3])
    if send_col.button("📨 Send this", use_container_width=True, type="primary"):
        st.session_state.pending = edited.strip()
        st.session_state.voice_draft = ""
        st.rerun()
    if clear_col.button("🗑️ Discard", use_container_width=True):
        st.session_state.voice_draft = ""
        st.session_state.last_voice = None
        st.rerun()


typed = st.chat_input("Ask a coding question, or paste an error…")
question = typed or st.session_state.pending
st.session_state.pending = None

if question:
    if not key_ready:
        st.error(
            "Add your OpenAI API key in the sidebar first — CodeSage needs it to think.",
            icon="🔑",
        )
        st.stop()

    # An attached screenshot counts as code context: it skips the classifier
    # call, and the system prompt handles a non-technical image.
    has_code = bool(code_input.strip()) or bool(images) or looks_like_code(question)

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(question)

    with st.chat_message("assistant", avatar=APP_ICON):
        try:
            # A cheap, deterministic model decides borderline scope questions.
            guard_llm = build_llm(
                model_name="gpt-4o-mini",
                temperature=0.0,
                streaming=False,
                api_key=active_api_key,
            )
            allowed, reason = is_coding_request(guard_llm, question, has_code)

            if not allowed:
                reply = refusal_message(question)
                st.markdown(reply)
                st.session_state.redirects += 1
            else:
                # Writing a whole app or game needs a much larger output
                # budget than a short answer — too small a cap truncates the
                # file mid-function and looks like broken logic.
                wants_long_output = mode in ("Generate", "Convert") or any(
                    word in question.lower()
                    for word in ("game", "build me", "create a", "full app",
                                 "whole app", "complete", "from scratch")
                )
                llm = build_llm(
                    model_name=model_name,
                    temperature=temperature,
                    streaming=True,
                    api_key=active_api_key,
                    long_output=wants_long_output,
                )
                inputs = {
                    "role_instruction": role_instruction,
                    "tech_context": build_tech_context(
                        question, code_input, stack_hint
                    ),
                    "mode_instruction": build_mode_instruction(mode, MODES),
                    "language_instruction": build_language_instruction(language),
                    "question": question,
                    "code_block": build_code_block(
                        code_input, LANGUAGE_HINTS.get(language)
                    ),
                }
                history = to_langchain_history(st.session_state.messages[:-1])
                reply = st.write_stream(
                    stream_answer(llm, inputs, history, images)
                )
                st.session_state.answers += 1

            if not (reply or "").strip():
                # An empty reply is a transient API hiccup, not an answer —
                # don't store it or the next turn sends a blank message.
                st.warning(
                    "The model returned an empty response. Hit **Regenerate** "
                    "or ask again — this is usually transient.",
                    icon="🫥",
                )
                st.session_state.messages.pop()
            else:
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )

        except Exception as exc:  # keep the app alive on any API problem
            st.error(f"Something went wrong talking to the model: {exc}", icon="🚨")
            st.caption(
                "Common causes: an invalid or out-of-quota API key, a model your "
                "account can't access, or no internet connection."
            )
            st.session_state.messages.pop()  # drop the unanswered user turn
