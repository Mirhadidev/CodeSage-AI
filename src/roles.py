"""Role validation — CodeSage will only wear a tech hat.

A user can assign any role they like ("Principal MERN stack developer",
"Django dev at a fintech"), but the role must be a technology / software one.
"You are an electrical engineer" is rejected, with a nearby coding role
suggested instead.

Same cheap-first strategy as the scope guard: heuristics decide the clear
cases with no API call, and only genuinely ambiguous role text is sent to a
one-word classifier.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

# Words that only ever show up in software roles. A hit here is decisive —
# it is what lets "electrical engineer who writes embedded firmware" through
# while plain "electrical engineer" is still rejected.
STRONG_TECH_TERMS = {
    # unambiguous titles
    "dev", "programmer", "coder", "software", "sde", "swe", "sdet",
    "techlead", "cto", "sysadmin",
    # disciplines
    "frontend", "front-end", "backend", "back-end", "fullstack", "full-stack",
    "full stack", "web", "mobile", "devops", "sre", "platform", "infra",
    "infrastructure", "cloud", "data", "database", "dba", "security",
    "appsec", "pentester", "qa", "testing", "automation", "embedded",
    "firmware", "systems", "network", "game", "graphics", "blockchain",
    "web3", "ml", "machine learning", "ai", "nlp", "computer vision",
    "prompt", "llm", "mlops", "etl", "analytics", "bioinformatics",
    # stacks & languages
    "mern", "mean", "lamp", "python", "django", "flask", "fastapi", "java",
    "spring", "kotlin", "javascript", "typescript", "react", "angular",
    "vue", "svelte", "next.js", "nextjs", "node", "nodejs", "express",
    "php", "laravel", "ruby", "rails", "golang", "go", "rust", "c++", "cpp",
    "c#", ".net", "dotnet", "swift", "ios", "android", "flutter", "dart",
    "unity", "unreal", "sql", "nosql", "mongodb", "postgres", "postgresql",
    "mysql", "redis", "kafka", "spark", "hadoop", "aws", "azure", "gcp",
    "docker", "kubernetes", "k8s", "terraform", "linux", "api", "rest",
    "graphql", "microservices", "solidity", "wordpress", "shopify",
    "salesforce", "sap abap", "powerbi", "tableau",
}

# Generic job words that mean nothing on their own — "engineer" fits both
# "software engineer" and "civil engineer". These never decide the verdict.
WEAK_TITLE_TERMS = {
    "engineer", "developer", "architect", "analyst", "scientist",
    "consultant", "administrator", "manager", "lead", "specialist",
    "researcher", "intern", "student", "freelancer",
}

# Multi-word phrases that are decisively technical.
STRONG_TECH_PHRASES = (
    "full stack", "machine learning", "computer vision", "computer science",
    "tech lead", "software", "web dev", "data science", "data scientist",
    "data engineer", "data analyst", "prompt engineer", "site reliability",
    "solutions architect", "software architect", "cloud architect",
    "systems architect", "security architect", "technical writer",
)

# Roles that are clearly outside software, unless a tech term also appears.
NON_TECH_PATTERNS = [
    r"\belectrical\b", r"\bmechanical\b", r"\bcivil\b", r"\bstructural\b",
    r"\bchemical\b", r"\baerospace\b", r"\bautomotive\b", r"\bmining\b",
    r"\bpetroleum\b", r"\bindustrial engineer", r"\bbiomedical\b",
    r"\bdoctor\b", r"\bphysician\b", r"\bsurgeon\b", r"\bnurse\b",
    r"\bdentist\b", r"\bpharmacist\b", r"\bveterinar", r"\bpsychiatrist\b",
    r"\bpsychologist\b", r"\btherapist\b", r"\bdietitian\b", r"\bnutritionist\b",
    r"\blawyer\b", r"\battorney\b", r"\bjudge\b", r"\bparalegal\b",
    r"\baccountant\b", r"\bauditor\b", r"\bbanker\b", r"\bfinancial advisor\b",
    r"\bstock broker\b", r"\breal estate\b", r"\binsurance agent\b",
    r"\bchef\b", r"\bcook\b", r"\bbaker\b", r"\bbarista\b", r"\bwaiter\b",
    r"\bplumber\b", r"\belectrician\b", r"\bcarpenter\b", r"\bwelder\b",
    r"\bmechanic\b", r"\bdriver\b", r"\bpilot\b", r"\bfarmer\b",
    r"\bteacher\b", r"\bprofessor\b", r"\blecturer\b", r"\btutor\b",
    r"\bjournalist\b", r"\bpoet\b", r"\bnovelist\b", r"\bscreenwriter\b",
    r"\bmusician\b", r"\bsinger\b", r"\bactor\b", r"\bpainter\b",
    r"\bphotographer\b", r"\bfashion\b", r"\binterior design",
    r"\bmarketer\b", r"\bmarketing manager\b", r"\bsalesperson\b",
    r"\bsales manager\b", r"\brecruiter\b", r"\bhr manager\b",
    r"\bhuman resources\b", r"\bcustomer service\b", r"\breceptionist\b",
    r"\bathlete\b", r"\bcoach\b", r"\btrainer\b", r"\bsoldier\b",
    r"\bpolice\b", r"\bfirefighter\b", r"\bpolitician\b", r"\bpriest\b",
    r"\bastrologer\b", r"\bchemist\b", r"\bbiologist\b", r"\bphysicist\b",
    r"\bgeologist\b", r"\bhistorian\b", r"\bphilosopher\b",
    # medical specialities (…ologist, minus "technologist")
    r"\bcardi\w*", r"\bonco\w*", r"\bderma\w*", r"\bradiolog\w*",
    r"\bneurolog\w*", r"\bgastro\w*", r"\burolog\w*", r"\bophthalm\w*",
    r"\banesthe\w*", r"\bpediatric\w*", r"\bclinical\b", r"\bmedical\b",
]

# Nearest coding role to offer when a non-tech role is rejected.
SUGGESTION_MAP = [
    (r"electrical|electronic|circuit", "Embedded / Firmware Engineer"),
    (r"mechanical|robotic|automotive|aerospace", "Robotics & Simulation Engineer"),
    (r"civil|structural|architect(?!ure of software)", "CAD / Geospatial Software Developer"),
    (r"chemical|chemist|biolog|bioinformat|pharma", "Scientific Computing / Bioinformatics Engineer"),
    (r"doctor|physician|nurse|medical|health|dentist|clinic|surgeon|"
     r"cardi|onco|derma|radiolog|neurolog|pediatric|anesthe|psychiat|therap",
     "Health-tech Backend Developer"),
    (r"chef|cook|baker|restaurant|barista|culinary", "Food-delivery Platform Developer"),
    (r"lawyer|attorney|legal|paralegal", "Legal-tech Software Engineer"),
    (r"account|audit|bank|financ|insurance|invest", "FinTech Backend Developer"),
    (r"teacher|professor|tutor|lecturer|educat", "Computer Science Educator"),
    (r"market|sales|advertis|seo", "Marketing Analytics Engineer"),
    (r"hr|recruit|human resources", "HR-tech Platform Developer"),
    (r"design|fashion|interior|photograph|artist|painter", "Frontend / UI Engineer"),
    (r"journalis|writer|poet|novelist|content", "Technical Writer (developer docs)"),
    (r"music|audio|sound|singer", "Audio / DSP Software Engineer"),
    (r"game|sport|athlete|coach", "Game Developer (Unity/Unreal)"),
    (r"physic|geolog|astronom|math", "Computational Science Engineer"),
]

DEFAULT_SUGGESTIONS = [
    "Senior Python Engineer",
    "Principal MERN Stack Developer",
    "DevOps / Cloud Engineer",
]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.\-]+", _normalise(text)))


def _has_strong_tech(text: str) -> bool:
    lowered = _normalise(text)
    if _words(text) & STRONG_TECH_TERMS:
        return True
    return any(phrase in lowered for phrase in STRONG_TECH_PHRASES)


def _has_weak_title(text: str) -> bool:
    return bool(_words(text) & WEAK_TITLE_TERMS)


def _has_non_tech_term(text: str) -> bool:
    lowered = _normalise(text)
    return any(re.search(p, lowered) for p in NON_TECH_PATTERNS)


def suggest_alternative(role: str) -> str:
    """The closest tech role to a rejected one."""
    lowered = _normalise(role)
    for pattern, suggestion in SUGGESTION_MAP:
        if re.search(pattern, lowered):
            return suggestion
    return DEFAULT_SUGGESTIONS[0]


def heuristic_role_verdict(role: str) -> bool | None:
    """True = tech role, False = not tech, None = let the classifier decide."""
    text = _normalise(role)
    if not text:
        return True

    # A decisive software signal wins even next to a non-tech word — that is how
    # "electrical engineer who writes embedded firmware in C" is accepted.
    if _has_strong_tech(text):
        return True

    # Clearly outside computing, with no software signal to rescue it.
    if _has_non_tech_term(text):
        return False

    # Only a generic title like "engineer" or "consultant" — too vague to judge.
    return None


def classify_role_with_llm(llm, role: str) -> bool:
    """One-word classifier for role text the heuristics can't place."""
    from .prompts import ROLE_GUARD_PROMPT

    try:
        verdict = llm.invoke(ROLE_GUARD_PROMPT.format(role=role[:300])).content
        return "NOT_TECH" not in verdict.strip().upper()
    except Exception:
        return True  # fail open — never block on an API hiccup


def validate_role(role: str, llm=None) -> tuple[bool, str]:
    """Return (accepted, reason)."""
    verdict = heuristic_role_verdict(role)
    if verdict is True:
        return True, "heuristic: tech role"
    if verdict is False:
        return False, "heuristic: non-tech role"
    if llm is None:
        return True, "unverified (no model available)"
    accepted = classify_role_with_llm(llm, role)
    return accepted, f"classifier: {'TECH' if accepted else 'NOT_TECH'}"
