# 🧠 CodeSage AI

**Your smart coding companion — review, debug, optimise, explain.**
A LangChain + Streamlit chat assistant that only talks about code.

> CodeSage AI is a coding assistant only. Always test generated code before
> using it in production.

---

## What it does

Paste code (or just describe a problem) and CodeSage will:

| Mode | What you get |
|---|---|
| ✨ **Auto** | CodeSage decides what you need |
| 🛠️ **Generate** | Describe a task → complete, runnable code with a usage example |
| 📖 **Explain** | Line-by-line walkthrough, jargon defined in plain words |
| 🐞 **Find bugs** | Real defects, each with a concrete failing scenario and a fix |
| ⚡ **Optimise** | A faster/cleaner version plus what actually improved |
| 🔀 **Alternatives** | Two or three different approaches, and which to pick |
| 🔍 **Review** | Structured review: correctness, readability, security |
| 🌍 **Convert** | Translate code idiomatically between languages |

It understands large, complex or unfamiliar code, and explains technical terms
on request.

### Choosing a model (this matters more than anything)

The sidebar has a **🧭 Which model should I pick?** panel, because picking the
wrong model is the single biggest cause of a bad answer:

| Task | Model |
|---|---|
| 🐞 Find bugs / Review | `gpt-4o` |
| 🛠️ Generate code | `gpt-4o` (or `gpt-4.1` for something large) |
| ⚡ Optimise / refactor | `gpt-4o` (`gpt-5` for tricky performance work) |
| 📖 Explain / learn | `gpt-4o-mini` — cheap is fine, no code is changed |
| 🌍 Convert language | `gpt-4.1` |
| 🧠 Hard or subtle bugs | `gpt-5` |
| 🎮 A whole app or game | `gpt-5` or `o3` |

Rule of thumb: cheap models are fine when nothing gets changed. Anything that
**judges or edits** your code deserves `gpt-4o` or better — a small model will
confidently invent bugs in working code. The default is `gpt-4o` for that
reason, and picking a weak model together with a review mode shows a warning.

Three rules in the system prompt back this up: lead every review with a verdict
(`✅ No real bugs found` is a valid answer), only report an issue if you can name
the inputs that make it fail, and **never regress working code** — don't call an
API invalid unless certain, and don't swap a modern call for an older one.

### Building a whole app or game

Two things were wrong when asked for something like a playable Ludo board:

**The output cap was too low.** `max_tokens` was 3000 — roughly 250 lines. A
board plus rules plus rendering does not fit, so the file was cut off
mid-function, which reads as broken logic rather than a truncation. Now 8000 for
ordinary answers and **16000 for code generation**, chosen automatically when the
mode is Generate/Convert or the question sounds like a build ("game", "create a",
"from scratch").

**It coded before it thought.** Generate mode now requires a plan first: name
the state model, list the rules explicitly (for Ludo: a 6 to leave the yard, a 6
grants another roll, landing on an opponent sends it home, safe squares, exact
count to finish), spell out the turn flow, and only then write code — keeping
those rule names as functions so a reader can check each one exists. It must end
with *"Not implemented / simplified:"* and 3-4 things to test first, and prefer a
smaller complete scope (two players) over a broken whole.

### When the model misbehaves

Language models occasionally get stuck repeating themselves — *"six six six
six…"* until the token limit. It is a decoding glitch, not a prompt problem, and
it happens most with near-greedy decoding. Four defences:

1. **Temperature 0.3 by default**, not 0.1. A little randomness is what breaks a
   repetition loop; near-greedy decoding is what causes them.
2. **A frequency penalty (0.2)** discourages re-emitting the same tokens. Sent
   only to model families that accept it — reasoning models reject the penalty
   knobs.
3. **A live loop-breaker.** `find_repetition()` in `src/utils.py` watches the
   stream and cuts it the moment the tail becomes one short string repeated over
   and over, replacing the garbage with a short explanation. It is deliberately
   conservative — code and prose legitimately repeat lines, so short units must
   repeat 12+ times to trigger. Tested against repeated `print()` lines, repeated
   markdown bullets and "very very" prose: no false positives.
4. **A hard `max_tokens` ceiling (8000, or 16000 for code generation)** so a loop that slips past everything
   else still cannot run away and bill you for it.

Plus a **🔄 Regenerate** button, so a bad answer costs one click instead of
retyping, and an empty response is never stored as a message.

### Talk instead of typing

Hit **🎙️ Speak**, record your question, and it comes back as text you can edit
before it sends. Built on `st.audio_input` plus OpenAI transcription.

Two details that matter:

* **A coding vocabulary prompt.** Speech models are trained on ordinary speech,
  so spoken code terms come back mangled — *"useEffect"* → *"use effect"*,
  *"async"* → *"a sync"*, *"TypeScript"* → *"type script"*. The transcription
  endpoint accepts a `prompt` that biases decoding toward expected words, so
  `src/voice.py` hands it a list of programming terms. That single parameter is
  the difference between a usable transcript and a frustrating one.
* **Review before send.** The transcript lands in an editable box with Send and
  Discard, rather than firing straight off — speech gets code terms wrong often
  enough that sending blind would waste requests.

Each clip is fingerprinted and transcribed exactly once. Streamlit reruns the
script constantly and the recording stays in the widget, so without that guard
the same audio would be re-sent (and re-billed) on every rerun.

### Screenshots instead of typing

**Paste straight from the clipboard** (Win+Shift+S, click the paste zone,
Ctrl+V) or browse for a file. Either way CodeSage reads the code, error dialog
or terminal trace out of the image — no retyping.

Paste needed a small custom component (`src/paste.py` + `src/paste_zone/`):
`st.file_uploader` can't accept a clipboard paste, because the browser only
fires a `paste` event at focused DOM and the uploader doesn't listen for one.
The component is a single HTML file that catches the paste, reads the image, and
returns a data URL to Python through Streamlit's component message protocol —
implemented by hand in three `postMessage` calls, so there's no npm build step
and no third-party package. Up to 3 images, 8 MB each, sent at high detail so small
code text stays legible.

* Needs a vision-capable model (gpt-4o and newer). Pick a text-only model with
  images attached and the app says so instead of silently dropping them.
* The answer transcribes the relevant code back into a fenced block, so you can
  copy the fix rather than retyping from a picture.
* Unreadable lines are called out rather than guessed at.
* The domain rule still applies: a screenshot of something non-technical is
  declined the same way an off-topic question is.

### It knows about *current* versions

The common failure of a simple custom-GPT wrapper: you ask about **React 19**,
assign the role "senior MERN developer", and it still answers with React 17
habits — `forwardRef`, `Context.Provider`, `defaultProps` — sounding completely
confident. The role prompt doesn't fix this. The model isn't disobeying; its
training data simply contains many more years of old tutorials than new ones.

CodeSage attacks that on three fronts:

1. **A target-stack box.** Pin `React 19, Next.js 15, Tailwind v4` and those
   versions are stated in the system prompt as the versions in use.
2. **A built-in version pack** (`src/tech_notes.py`). Mention a stack in your
   question or paste code that uses it, and short factual notes about its current
   major version are injected as authoritative context — *"`ref` is a normal prop,
   `forwardRef` is no longer needed"*, *"`cookies()` is async in Next 15"*,
   *"Tailwind v4 configures in CSS via `@theme`"*. Covers React, Next.js,
   Tailwind, Express, Node, Python, Django, TypeScript, Vue, Angular, Svelte,
   pandas, LangChain and the OpenAI SDK. The UI shows a 📌 line when notes load,
   so grounding is visible rather than invisible.
3. **A version-discipline policy** at the top of the system prompt: write for the
   version named, treat the reference block as authoritative over recollection,
   never present a removed API as current, label legacy patterns as legacy, and
   say plainly when something may be past the model's knowledge instead of
   quietly falling back to an old API.

The notes are a snapshot (early 2026), so they age. Adding a stack is a few lines
in `TECH_NOTES` — a trigger regex and the facts that get answered wrong.

### Assign it a role

A dropdown of ready-made tech personas — *Senior Prompt Engineer*, *Principal
MERN Stack Developer*, *Python Django Developer*, *DevOps / Cloud Engineer* and
more — plus a **custom role** box for anything else.

The role must be a technology one. Type *"electrical engineer"* and CodeSage
declines and offers the nearest coding role instead:

> I can't take on the role of **electrical engineer** — CodeSage is a coding
> agent, so every role it wears has to be a technology one.
> Closest fit I *can* be: **Embedded / Firmware Engineer**.

Validation lives in `src/roles.py` and is deliberately careful about the word
*engineer*, which belongs to both worlds:

* **Strong signals decide.** `firmware`, `django`, `mern`, `kubernetes` and
  friends accept a role outright — which is why *"electrical engineer who writes
  embedded firmware in C"* is accepted while plain *"electrical engineer"* is not.
* **Generic titles never decide.** `engineer`, `manager`, `consultant`,
  `architect` on their own are treated as unknown and sent to the classifier.
* **Non-tech patterns reject**, each mapped to a suggested alternative
  (lawyer → Legal-tech Software Engineer, chef → Food-delivery Platform
  Developer, cardiologist → Health-tech Backend Developer).

Verdicts are cached per role string, so changing a setting doesn't re-bill you
for the same check.

### It stays on topic

CodeSage is deliberately **coding-only**. Ask it for a biryani recipe and it
politely declines and points you back to what it's good at. This is enforced in
two cheap stages (`src/guard.py`):

1. **Heuristics first, no API call.** Pasted code, fenced blocks, stack traces,
   error names and ~200 technical keywords are admitted instantly. Greetings and
   short follow-ups ("why?", "show me another way") pass too, so the chat feels
   natural.
2. **A tiny classifier call** only for genuinely ambiguous messages, answering
   `CODING` or `OTHER`.

If the classifier errors, the guard **fails open** — a real coding question is
never blocked because of an API hiccup.

---

## Requirements

**Python 3.10+** (3.12 recommended).

This project runs on the **current LangChain 1.x line**, not the older 0.3
series used by earlier projects:

| Package | Version |
|---|---|
| `streamlit` | ≥ 1.63 |
| `langchain` | ≥ 1.4 |
| `langchain-openai` | ≥ 1.6 |
| `langchain-core` | ≥ 1.6 |
| `python-dotenv` | ≥ 1.2 |
| `openai` | ≥ 1.0 (voice transcription) |

Two consequences worth knowing:

* **No `LLMChain`.** That class moved out of `langchain` into the legacy
  `langchain-classic` package in 1.x. Chains here are built with **LCEL**
  (`prompt | llm | StrOutputParser`), which is the modern API and gives
  streaming, batching and async for free.
* **No `langchain-community`.** That package is being sunset, so the SQLite
  cache is implemented directly on `BaseCache` from `langchain-core`
  (~30 lines in `src/cache_manager.py`) instead of importing a deprecated one.

---

## Setup

### Windows (PowerShell)

```powershell
# 1. Enter the project
cd codesage_ai

# 2. Create a Python 3.12 virtual environment
py -3.12 -m venv venv
venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) add your key so you don't retype it
copy .env.example .env
#    then edit .env and set OPENAI_API_KEY=sk-...

# 5. Run
streamlit run app.py
```

### macOS / Linux

```bash
cd codesage_ai
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then edit it
streamlit run app.py
```

The app opens at **http://localhost:8501**.

You don't actually need a `.env` file — you can paste your key into the sidebar
instead, which is how the deployed version is meant to be used.

Get a key at <https://platform.openai.com>. `.env` is git-ignored, so your real
key is never committed.

---

## Bring your own key

The sidebar has an **OpenAI API key** box. Key priority is:

1. Key typed into the sidebar (wins — so a public deployment never spends the
   owner's credits)
2. `OPENAI_API_KEY` in `.env`
3. `OPENAI_API_KEY` in Streamlit Cloud secrets

Keys typed in the sidebar live only in that browser session and are never
written to disk.

---

## Caching

`set_llm_cache()` registers **one global cache** that LangChain checks before
every call. An identical prompt returns instantly and makes no API request.

| | `InMemoryCache` | `SQLiteCache` |
|---|---|---|
| Class | `langchain_core.caches.InMemoryCache` | custom `BaseCache` subclass |
| Stored in | RAM | `codesage_cache.db` on disk |
| Speed | Fastest | Fast |
| Survives restart | No | Yes |
| Best for | One session | Reusing across sessions |

Switch between them (or turn caching off) in the sidebar. Note that **streamed**
answers bypass the cache — streaming responses aren't cacheable in LangChain —
so the cache mainly benefits the scope-guard classifier calls.

---

## Project structure

```
codesage_ai/
├── app.py                  # Streamlit UI — run this
├── requirements.txt
├── .env.example
├── README.md
├── .streamlit/
│   └── config.toml         # dark theme
└── src/
    ├── __init__.py
    ├── config.py           # settings, model catalogue, modes, roles, languages
    ├── prompts.py          # SystemMessage rules, ChatPromptTemplate, guard prompts
    ├── chains.py           # ChatOpenAI, LCEL chain, streaming
    ├── guard.py            # coding-only scope guard
    ├── roles.py            # tech-only role validation + suggestions
    ├── tech_notes.py       # current-version knowledge pack + stack detection
    ├── cache_manager.py    # InMemoryCache + SQLiteCache
    ├── styles.py           # all custom CSS (animated scene, glass panels)
    └── utils.py            # language detection, helpers
```

---

## How it works

1. You pick a **role** and a **mode**, and optionally paste code.
2. The **guard** decides whether the message is a coding request.
3. If it is, the role persona, mode instruction, language hint, your code and the
   recent conversation are assembled into a `ChatPromptTemplate`.
4. `ChatOpenAI` streams the answer back, rendered live with `st.write_stream()`.
5. Off-topic messages skip the model entirely and get a friendly redirect.

---

## The interface

The UI is a deep-space scene built with pure CSS — drifting aurora blobs, a
twinkling starfield, and glassmorphic panels floating on top. All of it lives in
`src/styles.py`, so the look can be changed without touching app logic. Colours
are defined once as CSS variables at the top of that file.

---

## Deploying to Streamlit Community Cloud

1. Push this folder to a **public GitHub repo** (make sure `.env` is *not*
   committed — `.gitignore` handles that).
2. Go to <https://share.streamlit.io> → **Create app** → pick your repo.
3. Set **Main file path** to `app.py`.
4. In **Advanced settings**, set the Python version to **3.12**.
5. Leave **Secrets empty** so every visitor brings their own key. (If you'd
   rather use your own key for everyone, add `OPENAI_API_KEY = "sk-..."` there.)
6. Click **Deploy**.

Free-tier apps sleep after a spell without traffic. Visitors just click the
"wake up" button and it restarts in under a minute.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'langchain.chains'`**
You're reading old tutorials — `LLMChain` isn't part of LangChain 1.x. This
project doesn't use it; chains are LCEL (`prompt | llm | parser`).

**Anything odd right after upgrading from an older LangChain**
Rebuild the environment cleanly rather than upgrading in place:

```powershell
Get-Process python, pythonw, streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
Remove-Item -Recurse -Force venv
py -3.12 -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**`Activate.ps1 cannot be loaded because running scripts is disabled`**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Prompt shows `(base)` instead of `(venv)`**
Conda's base environment is shadowing the venv. Run `conda deactivate` first,
then activate the venv. Verify with `(Get-Command python).Source`.

**"That doesn't look like an OpenAI key"**
Keys start with `sk-`. Copy the whole thing, with no trailing spaces.

**Model errors mentioning access or quota**
Your account may not have access to the selected model, or is out of credit.
Switch to `gpt-4o-mini` in the sidebar.
