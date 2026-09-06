"""Version-awareness pack.

The problem this solves: an LLM's training data is dominated by years of older
tutorials, so asked about React 19 it will happily answer with React 17 habits
(`forwardRef`, `Context.Provider`, `defaultProps`) and sound confident doing it.
The role prompt does not fix that — the model isn't being disobedient, it simply
has far more old material than new.

The fix here is retrieval-lite: short, factual notes about the *current* major
version of common stacks. When the user's question or code mentions a stack, its
note is injected into the system prompt as authoritative context, so the model
answers from the note instead of from the average of old blog posts.

These notes are a snapshot (early 2026) and are deliberately short — they cover
the things that most often change and most often get answered wrong. The system
prompt tells the model to trust them over its own recollection, and to flag
uncertainty for anything newer.
"""

from __future__ import annotations

import re

NOTES_AS_OF = "early 2026"

# Each entry: trigger regex -> current-version facts the model gets wrong most.
TECH_NOTES: dict[str, dict[str, str]] = {
    "react": {
        "trigger": r"\breact\b|\breactjs\b|\bjsx\b|\buse(?:State|Effect|Memo|Ref)\b",
        "current": "React 19",
        "notes": """React 19 is the current major line.
- `ref` is a normal prop on function components. `forwardRef` is NO LONGER needed.
- Render `<Context>` directly as the provider; `<Context.Provider>` is legacy.
- `use()` reads a promise or context, and may be called conditionally.
- Actions: `useActionState`, `useFormStatus`, `useOptimistic` for form/async state.
- `<title>`, `<meta>`, `<link>` render anywhere and hoist to <head>.
- Removed: string refs, legacy context, `propTypes`/`defaultProps` on function
  components (use default parameters), `ReactDOM.render` (use `createRoot`).
- The React Compiler is a separate, opt-in tool — not automatic.""",
    },
    "nextjs": {
        "trigger": (
            r"\bnext\.?js\b|\bnextjs\b|\bapp router\b|\bserver component"
            r"|\bnext\s+(?:app|project|1[3-9])\b|[\"']use client[\"']|\bgetServerSideProps\b"
        ),
        "current": "Next.js 15",
        "notes": """Next.js 15 is the current major line.
- `cookies()`, `headers()`, `draftMode()`, and page `params`/`searchParams` are
  ASYNC — they return promises and must be awaited.
- `fetch` is NO LONGER cached by default; opt in with `cache: 'force-cache'`.
  GET route handlers and the client router cache are also uncached by default.
- Ships with React 19 support; Turbopack dev is stable.
- App Router is the default; `pages/` still works but is the legacy path.""",
    },
    "tailwind": {
        "trigger": r"\btailwind\b",
        "current": "Tailwind CSS v4",
        "notes": """Tailwind CSS v4 is the current major line.
- CSS-first config: `@import "tailwindcss";` and a `@theme { }` block in CSS.
  A `tailwind.config.js` is no longer created by default.
- No more `@tailwind base/components/utilities` directives.
- New high-performance engine; native cascade layers and CSS variables for theme
  values (so tokens are readable at runtime).""",
    },
    "express": {
        "trigger": r"\bexpress(?:\.js)?\b",
        "current": "Express 5",
        "notes": """Express 5 is the current major line.
- Async middleware that rejects now forwards to the error handler automatically;
  the old manual try/catch-and-`next(err)` wrapper is unnecessary.
- Path matching moved to a newer path-to-regexp: bare `*` and unnamed wildcards
  are invalid — use named parameters like `/*splat` or `/:name(.*)`.
- Several long-deprecated methods (`res.send(status, body)`, `app.del`) removed.""",
    },
    "node": {
        "trigger": r"\bnode(?:\.js)?\b|\bnpm\b|\bpackage\.json\b",
        "current": "Node.js 22 LTS / 24",
        "notes": """Node 22 is LTS and Node 24 is the newer line.
- `require()` of ESM, a stable built-in test runner, `node --watch`, and a
  built-in `.env` loader (`node --env-file=.env`) are all available — no nodemon
  or dotenv needed for simple cases.
- `fetch`, `WebSocket` and `AbortController` are global; no node-fetch import.""",
    },
    "python": {
        "trigger": r"\bpython\s*3\.\d|\bpython\b(?!.*\bdjango\b)",
        "current": "Python 3.13 / 3.14",
        "notes": """Python 3.13 and 3.14 are the recent lines.
- 3.13 added an improved REPL, an experimental JIT, and a free-threaded
  (no-GIL) build. 3.12+ has `type` statement and PEP 695 generics syntax.
- Prefer `X | None` over `Optional[X]`, built-in generics (`list[int]`), and
  `tomllib` for TOML. `datetime.utcnow()` is deprecated — use
  `datetime.now(datetime.UTC)`.""",
    },
    "django": {
        "trigger": r"\bdjango\b",
        "current": "Django 5.x",
        "notes": """Django 5.x is the current line.
- Async views, async ORM methods (`aget`, `acreate`, `afilter`) are available.
- `django.utils.timezone.utc` is gone — use `datetime.timezone.utc`.
- Prefer `settings.STORAGES` over the older `DEFAULT_FILE_STORAGE` /
  `STATICFILES_STORAGE` settings.""",
    },
    "typescript": {
        "trigger": r"\btypescript\b|\bts\b(?=\s|$)|\.tsx?\b",
        "current": "TypeScript 5.x",
        "notes": """TypeScript 5.x is current.
- Decorators follow the ECMAScript standard (no `experimentalDecorators` needed).
- `const` type parameters, `satisfies`, and `using`/`await using` for disposables.
- `verbatimModuleSyntax` replaces `importsNotUsedAsValues`/`preserveValueImports`.""",
    },
    "vue": {
        "trigger": r"\bvue(?:\.?js)?\b|\bnuxt\b",
        "current": "Vue 3.5",
        "notes": """Vue 3.x (3.5+) is current; Vue 2 reached end of life.
- Composition API with `<script setup>` is the mainstream style.
- `defineModel()` for two-way binding; reactive props destructure is supported.
- Nuxt 3/4 is the current meta-framework line, not Nuxt 2.""",
    },
    "angular": {
        "trigger": r"\bangular\b",
        "current": "Angular 19+",
        "notes": """Modern Angular (v19+) looks very different from AngularJS-era code.
- Standalone components are the default; NgModules are optional/legacy.
- Signals (`signal`, `computed`, `effect`, `input()`, `output()`) are the
  reactive primitive; `@if` / `@for` control flow replaces `*ngIf` / `*ngFor`.
- `inject()` is preferred over constructor injection in many places.""",
    },
    "langchain": {
        "trigger": r"\blangchain\w*\b|\blcel\b|\bchatopenai\b|\bllmchain\b|\bprompttemplate\b",
        "current": "LangChain 1.x",
        "notes": """LangChain 1.x is the current line.
- `.invoke()` IS the standard way to call a model or chain — it is the Runnable
  interface, alongside `.stream()`, `.batch()` and their async `a*` versions.
  Never tell a user that `invoke` is wrong or non-standard.
- `.generate()` is the OLD low-level call. It takes a LIST OF MESSAGE LISTS, not
  a string, and returns an `LLMResult` with no `.content`. Swapping `invoke` for
  `generate` BREAKS working code — do not suggest it.
- `llm.invoke("some string")` and `llm.invoke([messages])` both work and return
  an `AIMessage`, so `.content` is correct on the result.
- `LLMChain`, `ConversationChain` and friends moved to `langchain-classic`.
  The modern pattern is LCEL: `prompt | llm | parser`.
- `langchain-community` is being sunset; prefer standalone integration packages
  (`langchain-openai`, etc.).
- `ChatOpenAI(model="...")` is the current parameter; `model_name` is legacy.
- Imports live under `langchain_core` (messages, prompts, runnables).""",
    },
    "openai_models": {
        "trigger": r"\bgpt-\d|\bgpt-4o\b|\bo[34]-mini\b|\bmodel\s*=\s*[\"\']gpt",
        "current": "OpenAI model names",
        "notes": """These model ids are REAL and current — never tell a user one of
them is a typo or "not a valid model name":
- gpt-4o, gpt-4o-mini
- gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
- gpt-5, gpt-5-mini, gpt-5-nano
- o3, o4-mini (reasoning models; they reject a custom `temperature`)
Older ids like gpt-4 and gpt-3.5-turbo still exist but are the legacy choice —
suggesting a user "correct" gpt-4o-mini to gpt-4 is a downgrade, not a fix.
If you do not recognise a model id, say you are not sure rather than declaring
it invalid.""",
    },
    "openai_sdk": {
        "trigger": r"\bopenai\b.*\b(sdk|api|client)\b|\bopenai\.ChatCompletion\b",
        "current": "OpenAI Python SDK v1+",
        "notes": """The OpenAI Python SDK v1+ is the current line.
- Instantiate a client: `client = OpenAI()`, then `client.chat.completions.create(...)`.
- The pre-1.0 module-level style (`openai.ChatCompletion.create`) is removed.
- The Responses API is the newer surface alongside chat completions.""",
    },
    "svelte": {
        "trigger": r"\bsvelte(?:kit)?\b",
        "current": "Svelte 5",
        "notes": """Svelte 5 is the current major line.
- Runes are the reactivity model: `$state`, `$derived`, `$effect`, `$props`.
- The old `export let` props and `$:` reactive statements are legacy syntax.""",
    },
    "streamlit": {
        "trigger": r"\bstreamlit\b|\bst\.\w+|\bsession_state\b|\bst_\w+",
        "current": "Streamlit — framework traps",
        "notes": """Streamlit rules that are constantly got wrong. Check these before
suggesting UI code:
- You CANNOT attach a custom CSS class to a Streamlit widget. `st.button(...)`
  renders without your class, so a rule like `.my-btn:hover` never applies and any
  animation on it is dead code. Style via the widget's data-testid instead
  (`[data-testid="stButton"] button { ... }`), and never claim a visual effect that
  depends on a class you cannot attach.
- A widget placed in a narrow `st.columns` ratio is SQUEEZED to that width. Wide
  controls (`st.audio_input`, `st.file_uploader`, charts, data editors) need roughly
  250px+ and become unusable in a 1-2 unit column. Put them in `st.popover`, an
  expander, or a full-width row instead.
- `st.chat_input` cannot be pre-filled from code. To place text in the box (from
  speech, a suggestion chip, etc.) use `st.text_input` with a `key`, or stage the
  text in session_state and send it on the next run.
- session_state for a widget key can only be set BEFORE that widget is created in
  the same script run. Setting it after raises StreamlitAPIException.
- A widget that stops being rendered loses its state.
- The script re-runs top to bottom on every interaction. Anything expensive (an API
  call on an uploaded file or recording) must be de-duplicated — hash the bytes and
  skip if unchanged — or it repeats and re-bills on every rerun.
- `st.rerun()` is needed after mutating state that widgets earlier in the script
  already read.""",
    },
    "pandas": {
        "trigger": r"\bpandas\b|\bdataframe\b|\bpd\.\w+|\bdf\.\w+",
        "current": "pandas 2.x",
        "notes": """pandas 2.x is current.
- `df.append()` was removed — use `pd.concat`.
- `inplace=True` is discouraged; copy-on-write semantics are the direction.
- PyArrow-backed dtypes are available for strings and nullable types.""",
    },
}


def detect_stacks(*texts: str, limit: int = 3) -> list[str]:
    """Return the keys of stacks mentioned across the given texts."""
    blob = " ".join(t for t in texts if t)
    if not blob.strip():
        return []

    hits: list[tuple[int, str]] = []
    for key, entry in TECH_NOTES.items():
        matches = re.findall(entry["trigger"], blob, flags=re.IGNORECASE)
        if matches:
            hits.append((len(matches), key))

    hits.sort(key=lambda pair: pair[0], reverse=True)
    return [key for _count, key in hits[:limit]]


def build_tech_context(question: str, code: str = "", stack_hint: str = "") -> str:
    """Assemble the version-awareness block for the system prompt."""
    keys = detect_stacks(stack_hint, question, code)

    pinned = (stack_hint or "").strip()
    parts: list[str] = []

    if pinned:
        parts.append(
            f"TARGET STACK (the user pinned this — treat it as the version in "
            f"use, and write code for it): {pinned}"
        )

    if keys:
        blocks = []
        for key in keys:
            entry = TECH_NOTES[key]
            blocks.append(f"[{entry['current']}]\n{entry['notes']}")
        parts.append(
            "CURRENT-VERSION REFERENCE (accurate as of "
            f"{NOTES_AS_OF} — trust these over your own recollection, which "
            "skews toward older versions):\n\n" + "\n\n".join(blocks)
        )

    return "\n\n".join(parts)
