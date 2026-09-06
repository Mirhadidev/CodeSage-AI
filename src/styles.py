"""All of CodeSage AI's custom CSS and HTML fragments.

Kept out of app.py so the app file stays readable. The look is a deep-space
scene: drifting aurora blobs, a twinkling starfield and a neon horizon grid,
with glassmorphic panels floating on top.
"""

from __future__ import annotations

SCENERY_CSS = """
<style>
/* ------------------------------------------------------------------ *
 *  Palette
 * ------------------------------------------------------------------ */
:root {
  --cs-bg:        #070B1A;
  --cs-bg-2:      #0B1030;
  --cs-violet:    #7C5CFF;
  --cs-cyan:      #22D3EE;
  --cs-pink:      #F472B6;
  --cs-mint:      #34D399;
  --cs-amber:     #FBBF24;
  --cs-text:      #E8ECFF;
  --cs-muted:     #9AA6D4;
  --cs-glass:     rgba(255, 255, 255, 0.055);
  --cs-glass-brd: rgba(148, 163, 255, 0.22);
}

/* ------------------------------------------------------------------ *
 *  The animated scene
 * ------------------------------------------------------------------ */
.stApp {
  background:
    radial-gradient(1200px 800px at 15% -10%, #1B1247 0%, transparent 55%),
    radial-gradient(1000px 700px at 90% 0%,  #06304A 0%, transparent 50%),
    radial-gradient(900px 900px at 50% 110%, #0B2C3D 0%, transparent 55%),
    linear-gradient(180deg, var(--cs-bg) 0%, var(--cs-bg-2) 60%, #050818 100%);
  background-attachment: fixed;
  color: var(--cs-text);
}

/* Drifting aurora clouds — large, soft, pastel */
.stApp::before {
  content: "";
  position: fixed;
  inset: -35%;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 18% 26%, rgba(167, 139, 250, 0.55), transparent 58%),
    radial-gradient(circle at 82% 22%, rgba(94, 234, 212, 0.42), transparent 56%),
    radial-gradient(circle at 68% 74%, rgba(244, 154, 200, 0.48), transparent 58%),
    radial-gradient(circle at 12% 80%, rgba(110, 231, 183, 0.38), transparent 55%),
    radial-gradient(circle at 46% 48%, rgba(124, 92, 255, 0.32), transparent 62%);
  filter: blur(84px);
  animation: csAurora 26s ease-in-out infinite alternate;
}
@keyframes csAurora {
  0%   { transform: translate3d(0, 0, 0) scale(1)     rotate(0deg);  opacity: 0.8; }
  50%  { transform: translate3d(3%, -3%, 0) scale(1.15) rotate(5deg); opacity: 1;   }
  100% { transform: translate3d(-3%, 3%, 0) scale(1.08) rotate(-4deg);opacity: 0.88;}
}

/* Twinkling starfield */
.stApp::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    radial-gradient(1.8px 1.8px at 6% 14%, rgba(255,255,255,0.95), transparent),
    radial-gradient(1.5px 1.5px at 14% 42%, rgba(200,225,255,0.8), transparent),
    radial-gradient(1.2px 1.2px at 24% 8%,  rgba(255,255,255,0.7), transparent),
    radial-gradient(2px 2px   at 33% 62%, rgba(255,255,255,0.85), transparent),
    radial-gradient(1.3px 1.3px at 44% 24%, rgba(226,210,255,0.75), transparent),
    radial-gradient(1.6px 1.6px at 56% 88%, rgba(255,255,255,0.8), transparent),
    radial-gradient(1.2px 1.2px at 63% 34%, rgba(190,240,255,0.7), transparent),
    radial-gradient(1.9px 1.9px at 74% 66%, rgba(255,255,255,0.9), transparent),
    radial-gradient(1.4px 1.4px at 84% 18%, rgba(220,200,255,0.8), transparent),
    radial-gradient(1.1px 1.1px at 92% 52%, rgba(255,255,255,0.65), transparent),
    radial-gradient(1.7px 1.7px at 96% 84%, rgba(190,230,255,0.85), transparent),
    radial-gradient(1.3px 1.3px at 4% 72%, rgba(255,255,255,0.7), transparent);
  animation: csTwinkle 6s ease-in-out infinite alternate;
}
@keyframes csTwinkle {
  0%   { opacity: 0.4; }
  100% { opacity: 1; }
}

/* Keep real content above the scene */
.main .block-container,
div[data-testid="stMainBlockContainer"],
section[data-testid="stSidebar"] { position: relative; z-index: 1; }

.main .block-container,
div[data-testid="stMainBlockContainer"] {
  padding-top: 3.4rem;
  max-width: 1080px;
}

/* Let the scene show through Streamlit's top bar */
header[data-testid="stHeader"],
[data-testid="stHeader"] {
  background: transparent !important;
  backdrop-filter: blur(6px);
  /* The header is transparent, so content scrolls visibly beneath it — but it
     would still swallow the clicks. Let pointer events fall through the empty
     area while keeping the header's own buttons clickable. */
  pointer-events: none;
}
[data-testid="stHeader"] button,
[data-testid="stHeader"] a,
[data-testid="stHeader"] [role="button"],
[data-testid="stToolbar"],
[data-testid="stToolbar"] * {
  pointer-events: auto;
}

/* ------------------------------------------------------------------ *
 *  Hero
 * ------------------------------------------------------------------ */
.cs-hero {
  position: relative;
  overflow: hidden;
  border-radius: 26px;
  padding: 2.6rem 2rem 2rem;
  margin-bottom: 1.1rem;
  background: linear-gradient(135deg, rgba(124,92,255,0.20), rgba(34,211,238,0.13) 45%, rgba(244,114,182,0.16));
  border: 1px solid var(--cs-glass-brd);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 24px 70px rgba(3, 6, 25, 0.65), inset 0 1px 0 rgba(255,255,255,0.12);
}
/* sweeping shimmer across the hero */
.cs-hero::after {
  content: "";
  position: absolute;
  top: 0; left: -60%;
  width: 45%; height: 100%;
  background: linear-gradient(105deg, transparent, rgba(255,255,255,0.11), transparent);
  animation: csSweep 6.5s ease-in-out infinite;
  pointer-events: none;
}
@keyframes csSweep {
  0%   { left: -60%; }
  55%  { left: 115%; }
  100% { left: 115%; }
}

.cs-hero-inner { position: relative; z-index: 2; text-align: center; }

.cs-orb {
  font-size: 3.2rem;
  display: inline-block;
  line-height: 1;
  filter: drop-shadow(0 0 26px rgba(124, 92, 255, 0.85));
  animation: csFloat 4s ease-in-out infinite;
}
@keyframes csFloat {
  0%, 100% { transform: translateY(0) rotate(-3deg); }
  50%      { transform: translateY(-12px) rotate(3deg); }
}

.cs-title {
  margin: 0.5rem 0 0.2rem;
  font-size: 2.9rem;
  font-weight: 850;
  letter-spacing: -0.03em;
  background: linear-gradient(92deg, #A78BFA, #22D3EE 32%, #34D399 58%, #F472B6 84%, #A78BFA);
  background-size: 260% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: csGradient 7s linear infinite;
}
@keyframes csGradient {
  to { background-position: 260% center; }
}

.cs-tagline {
  color: #CBD5FF;
  font-size: 1.03rem;
  margin: 0 0 1.3rem;
  opacity: 0.92;
}

.cs-chip-row { display: flex; flex-wrap: wrap; gap: 0.55rem; justify-content: center; }
.cs-chip {
  padding: 0.42rem 1rem;
  border-radius: 999px;
  font-size: 0.83rem;
  font-weight: 650;
  color: #DCE4FF;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(148,163,255,0.3);
  transition: transform .25s ease, box-shadow .25s ease, background .25s ease;
  cursor: default;
}
.cs-chip:hover {
  transform: translateY(-4px);
  background: rgba(124,92,255,0.24);
  box-shadow: 0 10px 24px rgba(124,92,255,0.4);
}

/* ------------------------------------------------------------------ *
 *  Glass panels & sidebar
 * ------------------------------------------------------------------ */
section[data-testid="stSidebar"],
div[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div:first-child {
  background: linear-gradient(180deg, rgba(20,16,58,0.42), rgba(7,11,26,0.52)) !important;
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-right: none;
}
/* colourful divider between sidebar and content */
section[data-testid="stSidebar"]::after {
  content: "";
  position: absolute;
  top: 0; right: 0; bottom: 0;
  width: 1.5px;
  background: linear-gradient(180deg,
    rgba(167,139,250,0.9), rgba(34,211,238,0.8) 35%,
    rgba(52,211,153,0.7) 65%, rgba(244,114,182,0.85));
  pointer-events: none;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #DDE4FF; }

div[data-testid="stExpander"] {
  border: 1.5px solid transparent !important;
  border-radius: 20px !important;
  background:
    linear-gradient(rgba(11,15,40,0.86), rgba(9,13,34,0.88)) padding-box,
    linear-gradient(125deg,
      rgba(167,139,250,0.85), rgba(34,211,238,0.7) 38%,
      rgba(52,211,153,0.6) 68%, rgba(244,114,182,0.8)) border-box !important;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 14px 40px rgba(3,6,25,0.5);
  overflow: hidden;
}

/* ------------------------------------------------------------------ *
 *  Chat bubbles
 * ------------------------------------------------------------------ */
div[data-testid="stChatMessage"] {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(148,163,255,0.18);
  border-radius: 20px;
  padding: 1rem 1.1rem;
  margin-bottom: 0.85rem;
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 32px rgba(3, 6, 25, 0.45);
  animation: csRise 0.35s ease both;
}
@keyframes csRise {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
/* user turns get a violet edge, assistant turns a cyan one */
div[data-testid="stChatMessage"]:has(img[alt="user avatar"]),
div[data-testid="stChatMessage"]:nth-child(odd) {
  border-left: 3px solid rgba(124,92,255,0.85);
}

div[data-testid="stChatMessage"] code {
  background: rgba(124,92,255,0.16);
  color: #C4B5FD;
  padding: 0.12em 0.4em;
  border-radius: 6px;
}
div[data-testid="stChatMessage"] pre {
  border: 1px solid rgba(148,163,255,0.22);
  border-radius: 14px;
  background: rgba(4, 7, 22, 0.85) !important;
}

/* ------------------------------------------------------------------ *
 *  Inputs & buttons
 * ------------------------------------------------------------------ */
.stTextArea textarea, .stTextInput input {
  background: rgba(9, 14, 38, 0.85) !important;
  border: 1px solid rgba(148,163,255,0.28) !important;
  border-radius: 14px !important;
  color: var(--cs-text) !important;
}
.stTextArea textarea {
  font-family: "JetBrains Mono", "Fira Code", ui-monospace, Menlo, Consolas, monospace !important;
  font-size: 0.86rem !important;
  line-height: 1.55 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: rgba(124,92,255,0.85) !important;
  box-shadow: 0 0 0 3px rgba(124,92,255,0.22) !important;
}

.stButton > button {
  border-radius: 12px;
  border: 1px solid rgba(148,163,255,0.3);
  background: linear-gradient(135deg, rgba(124,92,255,0.9), rgba(34,211,238,0.75));
  color: #FFFFFF;
  font-weight: 650;
  transition: transform .2s ease, box-shadow .2s ease, filter .2s ease;
}
.stButton > button:hover {
  transform: translateY(-2px);
  filter: brightness(1.08);
  box-shadow: 0 12px 26px rgba(124,92,255,0.45);
}

/* ------------------------------------------------------------------ *
 *  The command bar (chat input)
 *
 *  A floating glass capsule with a slowly rotating aurora border. The
 *  border is a conic gradient painted into the border-box, masked away
 *  from the padding-box, so the fill stays dark while the edge glows.
 * ------------------------------------------------------------------ */
@property --cs-angle {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: false;
}

/* Let the scene show through behind the bar instead of a flat slab.
   Streamlit puts an untagged solid-colour wrapper between stBottom and the
   block container — that direct child is what has to be cleared. */
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
  background: transparent !important;
}
[data-testid="stBottom"] {
  background: linear-gradient(
    to top,
    rgba(5, 8, 24, 0.88) 22%,
    rgba(5, 8, 24, 0.5) 58%,
    rgba(5, 8, 24, 0) 100%
  ) !important;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
[data-testid="stBottomBlockContainer"] {
  padding-bottom: 1rem !important;
  max-width: 1080px;
}

/* Keyboard hint under the bar */
[data-testid="stBottomBlockContainer"]::after {
  content: "⏎ send  ·  ⇧⏎ new line  ·  coding questions only";
  display: block;
  margin-top: 0.55rem;
  text-align: center;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  color: rgba(154, 166, 212, 0.6);
}

/* The capsule itself */
[data-testid="stChatInput"] {
  --cs-angle: 0deg;
  position: relative;
  border: 2px solid transparent !important;
  border-radius: 22px !important;
  background:
    linear-gradient(#0C1130, #080C22) padding-box,
    conic-gradient(
      from var(--cs-angle),
      #7C5CFF, #22D3EE, #34D399, #FBBF24, #F472B6, #7C5CFF
    ) border-box !important;
  animation: csBorderSpin 9s linear infinite;
  /* The aurora pool is drawn with outer shadows rather than a pseudo-element:
     a negative-z-index pseudo would paint *over* this element's own background
     (it establishes a stacking context) and wash out the field. */
  box-shadow:
    0 18px 45px rgba(3, 6, 25, 0.75),
    0 8px 30px -4px rgba(124, 92, 255, 0.35),
    0 8px 34px -6px rgba(34, 211, 238, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.07);
  transition: box-shadow .3s ease, transform .3s ease;
}
@keyframes csBorderSpin {
  to { --cs-angle: 360deg; }
}

/* Focus: lift, brighten, spin faster */
[data-testid="stChatInput"]:focus-within {
  transform: translateY(-2px);
  animation-duration: 3.5s;
  box-shadow:
    0 24px 60px rgba(3, 6, 25, 0.8),
    0 12px 42px -4px rgba(124, 92, 255, 0.6),
    0 12px 46px -6px rgba(34, 211, 238, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

/* Inner field — the capsule owns the frame, so strip the textarea's own */
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--cs-text) !important;
  font-size: 1rem !important;
  padding: 0.7rem 0.4rem 0.7rem 0.7rem !important;
  max-height: 200px;
  caret-color: #22D3EE;
}
[data-testid="stChatInput"] textarea::placeholder {
  color: rgba(154, 166, 212, 0.75) !important;
  letter-spacing: 0.01em;
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
  background: transparent !important;
  border: none !important;
}

/* Send button as a glowing orb */
[data-testid="stChatInputSubmitButton"] {
  background: linear-gradient(135deg, #7C5CFF, #22D3EE) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 50% !important;
  width: 38px !important;
  height: 38px !important;
  margin: 0 0.35rem 0.3rem 0 !important;
  box-shadow: 0 6px 18px rgba(124, 92, 255, 0.5);
  transition: transform .22s ease, box-shadow .22s ease, filter .22s ease;
}
[data-testid="stChatInputSubmitButton"]:hover:not(:disabled) {
  transform: scale(1.12) rotate(-8deg);
  filter: brightness(1.12);
  box-shadow: 0 10px 26px rgba(34, 211, 238, 0.6);
}
[data-testid="stChatInputSubmitButton"]:disabled {
  background: rgba(255, 255, 255, 0.08) !important;
  box-shadow: none;
}
[data-testid="stChatInputSubmitButton"] svg { fill: currentColor; }

/* Mode radio rendered as colourful pills */
div[role="radiogroup"] { gap: 0.45rem !important; flex-wrap: wrap; }
div[role="radiogroup"] > label {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(148,163,255,0.26);
  border-radius: 999px;
  padding: 0.36rem 0.9rem 0.36rem 0.55rem;
  transition: all .22s ease;
}
div[role="radiogroup"] > label:hover {
  background: rgba(124,92,255,0.2);
  transform: translateY(-2px);
}

/* Metric cards */
div[data-testid="stMetric"] {
  background: var(--cs-glass);
  border: 1px solid var(--cs-glass-brd);
  border-radius: 16px;
  padding: 0.85rem 1rem;
  backdrop-filter: blur(10px);
}

/* Section label */
.cs-label {
  font-size: 0.78rem;
  font-weight: 750;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--cs-muted);
  margin: 0.4rem 0 0.5rem;
}

/* Scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(124,92,255,0.75), rgba(34,211,238,0.6));
  border-radius: 999px;
}

/* Hide Streamlit chrome */
#MainMenu, footer { visibility: hidden; }

/* ------------------------------------------------------------------ *
 *  Floating app shell + colourful borders
 *
 *  The whole app sits as one rounded card over the starfield, so the
 *  scene shows around its edges instead of running edge-to-edge.
 * ------------------------------------------------------------------ */
[data-testid="stAppViewContainer"] {
  position: relative;
  z-index: 1;
  margin: 14px;
  height: calc(100vh - 28px);
  border-radius: 28px;
  border: 1.5px solid transparent;
  background:
    linear-gradient(rgba(8, 12, 32, 0.46), rgba(6, 10, 26, 0.56)) padding-box,
    linear-gradient(135deg,
      rgba(167,139,250,0.9), rgba(34,211,238,0.75) 30%,
      rgba(52,211,153,0.6) 55%, rgba(251,191,36,0.55) 75%,
      rgba(244,114,182,0.9)) border-box;
  box-shadow: 0 40px 110px rgba(0, 0, 0, 0.62);
  /* NOTE: no `overflow: hidden` here. It looks harmless — it would clip content
     to the rounded corners — but it also clips the dropdown portals Streamlit
     renders for selectbox/multiselect in the main area, so every dropdown
     silently refused to open. The corners still read as rounded because the
     inner content is padded well inside them. */
  backdrop-filter: blur(26px) saturate(1.15);
  -webkit-backdrop-filter: blur(26px) saturate(1.15);
}

/* Hero gets the same colourful edge */
.cs-hero {
  border: 1.5px solid transparent !important;
  /* tint over a dark base: the aurora behind is bright, and without an opaque
     layer under the tint the hero text and chips lose contrast. */
  background:
    linear-gradient(135deg, rgba(124,92,255,0.30), rgba(34,211,238,0.16) 45%,
                    rgba(244,114,182,0.26)) padding-box,
    linear-gradient(rgba(10,14,38,0.88), rgba(8,12,30,0.9)) padding-box,
    linear-gradient(120deg,
      rgba(167,139,250,0.95), rgba(34,211,238,0.8) 40%,
      rgba(52,211,153,0.65) 70%, rgba(244,114,182,0.95)) border-box !important;
}

/* Metric cards, code area and selects get visible tinted edges */
div[data-testid="stMetric"] {
  border: 1.5px solid transparent !important;
  background:
    linear-gradient(rgba(11,15,40,0.86), rgba(9,13,34,0.88)) padding-box,
    linear-gradient(135deg, rgba(167,139,250,0.7), rgba(34,211,238,0.55)) border-box !important;
}

.stTextArea textarea,
.stTextInput input,
div[data-baseweb="select"] > div,
div[data-baseweb="select"] > div:first-child {
  border: 2px solid transparent !important;
  background:
    linear-gradient(rgba(10,14,38,0.92), rgba(8,12,30,0.92)) padding-box,
    linear-gradient(120deg, rgba(167,139,250,0.95), rgba(34,211,238,0.8) 50%,
                    rgba(244,114,182,0.95)) border-box !important;
  border-radius: 14px !important;
  box-shadow: 0 6px 18px rgba(3,6,25,0.35);
}
.stTextArea textarea:focus,
.stTextInput input:focus {
  box-shadow: 0 0 0 3px rgba(124,92,255,0.25) !important;
}

/* Selected mode pill glows so the active choice is obvious at a glance */
div[role="radiogroup"] > label:has(input:checked) {
  background: rgba(34, 211, 238, 0.16) !important;
  border-color: rgba(34, 211, 238, 0.95) !important;
  box-shadow:
    0 0 0 3px rgba(34, 211, 238, 0.15),
    0 8px 24px rgba(34, 211, 238, 0.35);
}

/* Starter buttons: colourful outline instead of flat fill */
.stButton > button {
  border: 1.5px solid transparent !important;
  background:
    linear-gradient(rgba(14,19,48,0.9), rgba(10,14,36,0.9)) padding-box,
    linear-gradient(120deg, rgba(167,139,250,0.9), rgba(34,211,238,0.75) 50%,
                    rgba(244,114,182,0.85)) border-box !important;
  color: #E8ECFF !important;
}
.stButton > button:hover {
  background:
    linear-gradient(rgba(124,92,255,0.28), rgba(34,211,238,0.22)) padding-box,
    linear-gradient(120deg, rgba(167,139,250,1), rgba(34,211,238,0.95) 50%,
                    rgba(244,114,182,1)) border-box !important;
}

/* File uploader panel edge */
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
  border: 1.5px dashed rgba(148,163,255,0.5) !important;
  border-radius: 16px !important;
  background: rgba(255,255,255,0.035) !important;
}

/* Sidebar title picks up the gradient treatment */
section[data-testid="stSidebar"] h2 {
  background: linear-gradient(92deg, #A78BFA, #22D3EE 45%, #F472B6);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: csGradient 8s linear infinite;
}

/* ------------------------------------------------------------------ *
 *  Alignment & clipping fixes
 *
 *  Gradient borders are painted into the element's border-box, so any
 *  ancestor with overflow:hidden or a mismatched radius clips them and
 *  the edge looks cut. These rules give every bordered control the same
 *  radius as its wrapper and stop the wrappers from cropping.
 * ------------------------------------------------------------------ */

/* Breathing room inside the code panel so nothing touches its edge */
[data-testid="stExpanderDetails"] {
  padding: 0.4rem 1.15rem 1.15rem !important;
}

/* Wrappers must not crop their child's border or glow */
[data-testid="stElementContainer"],
[data-testid="stTextArea"],
[data-testid="stTextInput"],
[data-testid="stVerticalBlock"] {
  overflow: visible !important;
}

/* Radius has to match the child, or the corner shaves the border off */
[data-testid="stTextAreaRootElement"],
[data-testid="stTextInputRootElement"] {
  border-radius: 14px !important;
  overflow: hidden;
  background: transparent !important;
  border: none !important;
}

/* The native resize grip paints over the rounded corner and shows as a
   stray coloured wedge — size the textarea with the panel instead. */
.stTextArea textarea {
  resize: vertical;
  border-radius: 14px !important;
}
.stTextArea textarea::-webkit-resizer { background: transparent; }

/* Selects: same radius on the inner baseweb box and its wrapper */
div[data-baseweb="select"],
div[data-baseweb="select"] > div {
  border-radius: 14px !important;
}
div[data-baseweb="select"] > div { min-height: 44px; }

/* Inputs and selects share one height so a row lines up */
.stTextInput input { min-height: 44px; padding: 0.5rem 0.85rem !important; }

/* Paste zone: keep its dashed edge clear of the panel wall */
[data-testid="stIFrame"] { margin: 0.15rem 0; }

/* The uploader sits flush with the fields above it */
[data-testid="stFileUploaderDropzone"] { padding: 0.9rem 1rem !important; }

/* ------------------------------------------------------------------ *
 *  Voice input
 * ------------------------------------------------------------------ */
/* The Speak button reads as a mic control, not a generic button */
[data-testid="stPopover"] button {
  border: 2px solid transparent !important;
  border-radius: 999px !important;
  background:
    linear-gradient(rgba(14,19,48,0.92), rgba(10,14,36,0.92)) padding-box,
    linear-gradient(120deg, rgba(244,114,182,0.95), rgba(167,139,250,0.9) 60%,
                    rgba(34,211,238,0.85)) border-box !important;
  font-weight: 650 !important;
  transition: transform .2s ease, box-shadow .2s ease;
}
[data-testid="stPopover"] button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(244,114,182,0.4);
}

/* The recorder inside the popover */
[data-testid="stAudioInput"] {
  border: 1.5px solid rgba(244,114,182,0.45) !important;
  border-radius: 14px !important;
  background: rgba(244,114,182,0.07) !important;
  padding: 0.35rem 0.5rem !important;
}

/* While a clip is captured, the popover trigger keeps a soft pulse so it is
   obvious something is waiting to be sent. */
@keyframes csMicPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(244,114,182,0.45); }
  50%      { box-shadow: 0 0 0 8px rgba(244,114,182,0); }
}
[data-testid="stAudioInput"]:has(audio) { animation: csMicPulse 2s ease-out infinite; }
</style>
"""


def hero_html(icon: str, name: str, tagline: str) -> str:
    return f"""
<div class="cs-hero">
  <div class="cs-hero-inner">
    <div class="cs-orb">{icon}</div>
    <h1 class="cs-title">{name}</h1>
    <p class="cs-tagline">{tagline}</p>
    <div class="cs-chip-row">
      <span class="cs-chip">🛠️ Code generation</span>
      <span class="cs-chip">🐞 Bug hunting</span>
      <span class="cs-chip">📖 Code explained</span>
      <span class="cs-chip">⚡ Optimisation</span>
      <span class="cs-chip">🎭 Role-aware</span>
    </div>
  </div>
</div>
"""


def label(text: str) -> str:
    return f'<div class="cs-label">{text}</div>'
