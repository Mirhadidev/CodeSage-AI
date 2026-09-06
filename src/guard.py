"""Scope guard — keeps CodeSage AI on coding topics.

Two stages, cheapest first:

1. A heuristic pass. Obvious coding messages (code was pasted, a fenced block,
   a stack trace, strong technical keywords) are admitted with no API call, and
   obvious small talk is admitted too so greetings feel natural.
2. Anything still ambiguous goes to a tiny classifier LLM call that answers
   CODING or OTHER.

If the classifier errors for any reason we fail *open* (allow the message)
rather than wrongly refusing a real coding question.
"""

from __future__ import annotations

import re

from .prompts import GUARD_PROMPT

# --- stage 1 vocabulary ----------------------------------------------------

CODE_KEYWORDS = {
    # languages & ecosystems
    "python", "javascript", "typescript", "java", "kotlin", "swift", "golang",
    "rust", "php", "ruby", "scala", "perl", "haskell", "matlab", "dart",
    "html", "css", "sql", "bash", "shell", "powershell", "regex",
    # frameworks & libraries
    "react", "vue", "angular", "svelte", "django", "flask", "fastapi", "rails",
    "spring", "express", "nextjs", "node", "npm", "pip", "maven", "gradle",
    "pandas", "numpy", "pytorch", "tensorflow", "sklearn", "streamlit",
    "langchain", "pytest", "junit", "jest", "webpack", "vite", "tailwind",
    # concepts
    "function", "variable", "loop", "array", "list", "dict", "dictionary",
    "class", "method", "object", "recursion", "algorithm", "complexity",
    "pointer", "memory leak", "async", "await", "promise", "thread", "mutex",
    "compile", "compiler", "runtime", "syntax", "parser", "closure",
    "inheritance", "interface", "generic", "typing", "null", "undefined",
    "exception", "traceback", "stack trace", "stacktrace", "segfault",
    "refactor", "debug", "unit test", "endpoint", "api", "rest", "graphql",
    "json", "yaml", "xml", "query", "database", "schema", "migration",
    "index", "join", "orm", "cache", "docker", "kubernetes", "container",
    "git", "commit", "merge", "branch", "pull request", "repository", "repo",
    "deploy", "server", "backend", "frontend", "bug", "error", "crash",
    "optimize", "optimise", "performance", "latency", "big o",
    "code", "script", "program", "library", "framework", "package", "module",
}

# Errors and patterns that basically only appear in code contexts.
CODE_SIGNALS = [
    r"```",                              # fenced block
    r"\bdef\s+\w+\s*\(",                 # python def
    r"\bfunction\s+\w+\s*\(",            # js function
    r"\bclass\s+\w+",                    # class decl
    r"\b(?:const|let|var)\s+\w+\s*=",    # js binding
    r"\bimport\s+[\w.{]",                # import
    r"\bfrom\s+[\w.]+\s+import\b",
    r"#include\s*<",
    r"\bpublic\s+(?:static\s+)?\w+\s+\w+\s*\(",
    r"\bSELECT\b.+\bFROM\b",             # sql
    r"\w+Error\b|\w+Exception\b",        # exception names
    r"Traceback \(most recent call last\)",
    r"\bnpm\s+(?:install|run)\b|\bpip\s+install\b|\bgit\s+\w+",
    r"=>|::|->|\|\||&&|!==|===",         # operator soup
    r"</\w+>|<\w+\s+\w+=",               # markup
]

GREETINGS = {
    "hi", "hey", "hello", "yo", "hiya", "sup", "thanks", "thank you", "ty",
    "thx", "ok", "okay", "cool", "nice", "great", "awesome", "got it",
    "good morning", "good afternoon", "good evening", "bye", "goodbye",
    "who are you", "what can you do", "help", "what are you",
}

FOLLOW_UPS = {
    "why", "why?", "how", "how?", "explain", "explain that", "more",
    "continue", "go on", "again", "another way", "show me another way",
    "simpler", "make it simpler", "and?", "what about performance",
}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def heuristic_verdict(message: str, has_code: bool) -> str | None:
    """Return 'allow', 'greeting', or None when the LLM should decide."""
    if has_code:
        return "allow"

    text = message or ""
    lowered = _normalise(text)

    if not lowered:
        return "allow"

    # Strong structural signals — clearly code or an error dump.
    for pattern in CODE_SIGNALS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            return "allow"

    # Short conversational openers and thanks.
    stripped = lowered.rstrip("!.?")
    if stripped in GREETINGS or stripped in FOLLOW_UPS:
        return "greeting"

    # Keyword hit — treat as coding.
    words = set(re.findall(r"[a-z+#.]+", lowered))
    if words & CODE_KEYWORDS:
        return "allow"
    for phrase in ("stack trace", "pull request", "memory leak", "unit test", "big o"):
        if phrase in lowered:
            return "allow"

    # Very short follow-ups inside an ongoing chat are usually contextual.
    if len(lowered.split()) <= 3:
        return "allow"

    return None  # ambiguous → ask the classifier


def classify_with_llm(llm, message: str) -> bool:
    """True when the classifier says the message is a coding request."""
    try:
        prompt = GUARD_PROMPT.format(message=message[:2000])
        verdict = llm.invoke(prompt).content.strip().upper()
        return "OTHER" not in verdict
    except Exception:
        return True  # fail open — never block a real question over an API hiccup


def is_coding_request(llm, message: str, has_code: bool) -> tuple[bool, str]:
    """Return (allowed, reason). `reason` is useful for the sidebar debug line."""
    verdict = heuristic_verdict(message, has_code)
    if verdict == "allow":
        return True, "heuristic: coding signal"
    if verdict == "greeting":
        return True, "heuristic: greeting"
    allowed = classify_with_llm(llm, message)
    return allowed, f"classifier: {'CODING' if allowed else 'OTHER'}"
