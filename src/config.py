"""Settings, model catalogue and UI option lists for CodeSage AI."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "CodeSage AI"
APP_ICON = "🧠"
APP_TAGLINE = "Your smart coding companion — review, debug, optimise, explain."

DISCLAIMER = (
    "CodeSage AI is a coding assistant only. It reviews, debugs, explains and "
    "improves code. Always test generated code before using it in production."
)


def _get_setting(name: str, default: str = "") -> str:
    """Read a setting from the environment, then Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value
    try:  # pragma: no cover - only meaningful on Streamlit Cloud
        import streamlit as st

        return str(st.secrets.get(name, default))
    except Exception:
        return default


def is_valid_key(key: str) -> bool:
    """Loose sanity check so obvious typos are caught before an API call."""
    key = (key or "").strip()
    return key.startswith("sk-") and len(key) > 20


OPENAI_API_KEY = _get_setting("OPENAI_API_KEY", "")
DEFAULT_MODEL = _get_setting("DEFAULT_MODEL", "gpt-4o")
DEFAULT_TEMPERATURE = float(_get_setting("DEFAULT_TEMPERATURE", "0.3") or 0.3)

# Near-greedy decoding (temperature ~0) is a well-known cause of degenerate
# repetition — the model gets stuck emitting the same token forever ("six six
# six six…"). A small amount of randomness plus a frequency penalty breaks
# those loops, and a hard token cap stops one that starts anyway.
# 8000 is the floor for ordinary answers; a full game or app needs far more, so
# code-generation modes raise it (see GENERATE_OUTPUT_TOKENS). 3000 was too low
# — a Ludo board plus rules plus rendering does not fit, and a truncated file
# looks exactly like "the model wrote broken logic".
MAX_OUTPUT_TOKENS = int(_get_setting("MAX_OUTPUT_TOKENS", "8000") or 8000)
GENERATE_OUTPUT_TOKENS = int(_get_setting("GENERATE_OUTPUT_TOKENS", "16000") or 16000)
FREQUENCY_PENALTY = 0.2
PRESENCE_PENALTY = 0.0

# --------------------------------------------------------------------------
# Model catalogue
# --------------------------------------------------------------------------
MODEL_OPTIONS: dict[str, str] = {
    "gpt-4o": "Best all-rounder — the right default for review, debugging and fixes.",
    "gpt-4o-mini": "Fast and cheap. Good for explanations; weak at review — it invents bugs.",
    "gpt-4.1": "Strong on long files and multi-file reasoning. Slower.",
    "gpt-4.1-mini": "Cheaper 4.1. Decent balance for everyday help.",
    "gpt-4.1-nano": "Cheapest 4.1. Short answers and simple lookups only.",
    "gpt-5": "Deepest reasoning — hard bugs, whole apps, architecture. Slowest.",
    "gpt-5-mini": "Good reasoning at a lower price than gpt-5.",
    "gpt-5-nano": "Very fast and cheap. Simple questions only.",
    "o3": "Reasoning model — thinks before answering. Best for tricky logic.",
    "o4-mini": "Smaller reasoning model. Cheaper than o3, still deliberate.",
    "gpt-4-turbo": "Legacy. Only if you specifically need it.",
}

# Task-to-model guidance shown in the sidebar. Keeping it short and honest
# matters more than listing every model: picking the wrong model is the single
# biggest cause of a bad answer.
MODEL_GUIDE: list[tuple[str, str, str]] = [
    ("🐞 Find bugs / Review", "gpt-4o", "accuracy matters most here"),
    ("🛠️ Generate code", "gpt-4o", "or gpt-4.1 for something large"),
    ("⚡ Optimise / refactor", "gpt-4o", "gpt-5 for tricky performance work"),
    ("📖 Explain / learn", "gpt-4o-mini", "cheap is fine — no code is changed"),
    ("🌍 Convert language", "gpt-4.1", "handles long files well"),
    ("🧠 Hard or subtle bugs", "gpt-5", "concurrency, types, architecture"),
    ("🎮 A whole app or game", "gpt-5", "or o3 — lots of interacting rules"),
]

MODEL_WARNING_PREFIXES = ("gpt-4o-mini", "gpt-5-nano", "gpt-3.5")
REVIEW_MODES = ("Find bugs", "Review", "Optimise")

CUSTOM_MODEL_LABEL = "Custom…"

# Reasoning models reject a custom temperature.
NO_TEMPERATURE_PREFIXES = ("o1", "o3", "o4", "gpt-5")


def supports_temperature(model_name: str) -> bool:
    name = (model_name or "").strip().lower()
    return not name.startswith(NO_TEMPERATURE_PREFIXES)


# Model families that can read images. Anything else gets text only.
VISION_PREFIXES = ("gpt-4o", "gpt-4.1", "gpt-5", "o1", "o3", "o4")

# Screenshots are usually a few hundred KB; keep a sane ceiling so a giant
# PNG can't blow up the request.
MAX_IMAGE_MB = 8
MAX_IMAGES = 3


def supports_vision(model_name: str) -> bool:
    """True when the model can accept image input."""
    name = (model_name or "").strip().lower()
    return name.startswith(VISION_PREFIXES)


def model_help(model_name: str) -> str:
    return MODEL_OPTIONS.get(model_name, "Custom model id — make sure your account can access it.")


# --------------------------------------------------------------------------
# Assistant modes — these steer the system prompt
# --------------------------------------------------------------------------
MODES: dict[str, dict[str, str]] = {
    "Auto": {
        "icon": "✨",
        "blurb": "Let CodeSage decide what you need.",
        "instruction": (
            "Read the user's request and decide for yourself whether they want an "
            "explanation, a bug fix, a review, an optimisation or a rewrite. "
            "Answer in whichever shape genuinely helps most.\n"
            "IF the request is a review or bug hunt ('any bugs?', 'is this ok?', "
            "'anything worth fixing?'), apply full review discipline even though "
            "the mode is Auto:\n"
            "  - START with a verdict line: '✅ No real bugs found' / "
            "'⚠️ N issue(s) found'.\n"
            "  - Only list something as an issue if you can name the inputs or "
            "state that make it actually misbehave. Style preferences, naming and "
            "docstring consistency are NOT bugs — put them under 'Minor / "
            "optional', or leave them out.\n"
            "  - VERIFY before you claim. Do not say an import is unused without "
            "checking the rest of the file for it. Do not call a return type wrong "
            "when the function is deliberately shaped that way.\n"
            "  - Never pad a review to look thorough. Two real findings beat five "
            "invented ones, and zero findings is a valid answer."
        ),
    },
    "Generate": {
        "icon": "🛠️",
        "blurb": "Describe a task — get complete, runnable code.",
        "instruction": (
            "Write new code for the task the user describes. Produce a complete, "
            "runnable solution rather than a fragment: include the imports, the entry "
            "point, and a short usage example. State any assumption you had to make in "
            "one line before the code. After the code, add a brief 'How it works' note "
            "of two or three sentences and mention what you would add next for "
            "production (tests, error handling, config) without writing all of it. "
            "If the request is too vague to code against, ask ONE focused question and "
            "give your best attempt anyway — never stall on a blank reply.\n"
            "\n"
            "FOR A WHOLE APP OR GAME (many interacting rules), work in this order "
            "before writing a single line:\n"
            "  1. STATE MODEL — name every piece of state you will keep and its "
            "shape (board, pieces, whose turn, dice value, phase). Most broken "
            "games come from state that was never modelled.\n"
            "  2. RULES — list the rules you are implementing as short bullets, "
            "including the awkward ones. For Ludo that means: a 6 is needed to "
            "leave the yard; a 6 grants another roll; landing on an opponent "
            "sends it home; safe squares; exact count needed to finish.\n"
            "  3. TURN FLOW — spell out the loop: roll → legal moves → if none, "
            "pass → apply move → check captures → check win → next player.\n"
            "  4. THEN code it, keeping the rules from step 2 as functions with "
            "the same names, so a reader can check each rule was implemented.\n"
            "  5. END with 'Not implemented / simplified:' listing honestly what "
            "you left out, and 3-4 specific things to test first.\n"
            "Do not silently drop a rule you listed. If the code would be too long, "
            "implement a smaller but COMPLETE scope (two players instead of four) "
            "and say so — a working subset beats a broken whole."
        ),
    },
    "Explain": {
        "icon": "📖",
        "blurb": "Walk through what the code does, line by line.",
        "instruction": (
            "Explain the code clearly. Start with a one-paragraph summary of what it "
            "does overall, then walk through the important parts in order. Define any "
            "jargon or language-specific terms in plain words. Do not rewrite the code "
            "unless the user asks — the goal is understanding."
        ),
    },
    "Find bugs": {
        "icon": "🐞",
        "blurb": "Hunt for errors, edge cases and crashes.",
        "instruction": (
            "Act as a careful reviewer hunting for REAL defects.\n"
            "START with a one-line verdict: '✅ No real bugs found' or "
            "'⚠️ N issue(s) found'. Then list only the issues that survive this test: "
            "you can name specific inputs or state that make the code actually "
            "misbehave. If you cannot describe a concrete failure, it is NOT a bug — "
            "leave it out or put it under a short 'Minor / optional' heading clearly "
            "marked as not a defect.\n"
            "For each real issue give: what is wrong, the concrete failing scenario, "
            "and the corrected code. Most severe first.\n"
            "Finding nothing is a valid result. Say so and stop — do not pad the list."
        ),
    },
    "Optimise": {
        "icon": "⚡",
        "blurb": "Make it faster, cleaner, more efficient.",
        "instruction": (
            "Improve the code's efficiency and clarity. Show the optimised version, "
            "then explain what changed and why it is better — mention time/space "
            "complexity when it genuinely changes. Do not sacrifice readability for "
            "micro-optimisations, and say so when a change is not worth it.\n"
            "If the code is already efficient for its purpose, say exactly that "
            "instead of rewriting it for the sake of showing a diff."
        ),
    },
    "Alternatives": {
        "icon": "🔀",
        "blurb": "Show simpler or different ways to do it.",
        "instruction": (
            "Offer two or three genuinely different ways to solve the same problem — "
            "for example a simpler beginner-friendly version, an idiomatic version, and "
            "a library-based version. For each, show the code and give one line on when "
            "you would pick it. End with your own recommendation."
        ),
    },
    "Review": {
        "icon": "🔍",
        "blurb": "Full code review: style, structure, safety.",
        "instruction": (
            "Give a structured code review covering correctness, readability, "
            "structure, naming, error handling and security.\n"
            "START with a one-line verdict: '✅ Looks solid' / '⚠️ Some fixes needed' "
            "/ '🚨 Serious problems'. Then group feedback under short headings and "
            "label every point Critical, Should fix, or Nice to have — and be honest "
            "about the split: a well-written file should come back mostly 'Nice to "
            "have', with an empty Critical section.\n"
            "Say plainly what is done well; that is information too. Never invent a "
            "Critical item to make the review look thorough."
        ),
    },
    "Convert": {
        "icon": "🌍",
        "blurb": "Translate code between languages.",
        "instruction": (
            "Translate the code into the target language the user names, keeping the "
            "same behaviour. Write idiomatic code for the target language rather than a "
            "literal line-by-line port, and call out anything that cannot translate "
            "cleanly (missing library, different concurrency model, and so on)."
        ),
    },
}

LANGUAGES = [
    "Auto-detect",
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C",
    "C++",
    "C#",
    "Go",
    "Rust",
    "PHP",
    "Ruby",
    "Swift",
    "Kotlin",
    "SQL",
    "HTML/CSS",
    "Bash / Shell",
    "R",
    "Other",
]

# Streamlit's code block wants a lowercase language hint.
LANGUAGE_HINTS = {
    "Auto-detect": None,
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "Java": "java",
    "C": "c",
    "C++": "cpp",
    "C#": "csharp",
    "Go": "go",
    "Rust": "rust",
    "PHP": "php",
    "Ruby": "ruby",
    "Swift": "swift",
    "Kotlin": "kotlin",
    "SQL": "sql",
    "HTML/CSS": "html",
    "Bash / Shell": "bash",
    "R": "r",
    "Other": None,
}

STARTER_PROMPTS = [
    "Build a REST API for a todo app",
    "Why does my loop skip the last item?",
    "Explain what a Python decorator does",
    "Make this SQL query faster",
]

# ---------------------------------------------------------------------------
# Role assignment — the persona CodeSage answers as.
# Only tech / engineering roles are accepted (see src/roles.py).
# ---------------------------------------------------------------------------
NO_ROLE_LABEL = "No specific role"
CUSTOM_ROLE_LABEL = "Custom role…"

ROLE_PRESETS: dict[str, str] = {
    NO_ROLE_LABEL: "",
    "Senior Prompt Engineer": (
        "a senior prompt engineer who designs, tests and hardens LLM prompts and "
        "agent pipelines"
    ),
    "Principal MERN Stack Developer": (
        "a principal MERN stack developer (MongoDB, Express, React, Node.js) who has "
        "shipped and scaled production web apps"
    ),
    "Python Django Developer": (
        "a Django specialist who knows the ORM, migrations, DRF and Django's security "
        "model inside out"
    ),
    "Senior Python Engineer": (
        "a senior Python engineer who cares about clean, idiomatic, well-tested code"
    ),
    "Frontend React Engineer": (
        "a frontend engineer expert in React, state management, accessibility and "
        "browser performance"
    ),
    "Backend Node.js Engineer": (
        "a backend Node.js engineer experienced with APIs, async patterns and "
        "database design"
    ),
    "Java Spring Boot Developer": (
        "a Java engineer fluent in Spring Boot, dependency injection and JVM tuning"
    ),
    "DevOps / Cloud Engineer": (
        "a DevOps engineer fluent in Docker, Kubernetes, CI/CD pipelines and cloud "
        "infrastructure"
    ),
    "Data Engineer": (
        "a data engineer who builds reliable pipelines, warehouses and SQL at scale"
    ),
    "Machine Learning Engineer": (
        "an ML engineer who ships models to production, not just notebooks"
    ),
    "Mobile Developer (Flutter)": (
        "a mobile developer expert in Flutter, Dart and cross-platform app patterns"
    ),
    "Database / SQL Specialist": (
        "a database specialist focused on schema design, indexing and query "
        "optimisation"
    ),
    "Security Engineer": (
        "an application security engineer who thinks in threat models and secure "
        "defaults"
    ),
    "QA Automation Engineer": (
        "a QA automation engineer who writes robust, non-flaky test suites"
    ),
    "Software Architect": (
        "a software architect who weighs tradeoffs across systems, not just files"
    ),
    CUSTOM_ROLE_LABEL: "",
}
