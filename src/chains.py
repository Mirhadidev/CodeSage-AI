"""ChatOpenAI setup, the reusable LLMChain, and the streaming generator."""

from __future__ import annotations

from typing import Iterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from .config import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    FREQUENCY_PENALTY,
    GENERATE_OUTPUT_TOKENS,
    MAX_OUTPUT_TOKENS,
    OPENAI_API_KEY,
    PRESENCE_PENALTY,
    supports_temperature,
)
from .prompts import ANSWER_CHAT_TEMPLATE, ANSWER_PROMPT

# ---------------------------------------------------------------------------
# Chain construction — LCEL.
#
# LangChain 1.x is the current line, and the old `LLMChain` class moved out of
# `langchain` into the legacy `langchain-classic` package. The modern way to
# compose a chain is LCEL: `prompt | llm | parser`, which is a Runnable with
# built-in streaming, batching and async support.
# ---------------------------------------------------------------------------
CHAIN_SOURCE = "LCEL — prompt | llm | StrOutputParser (LangChain 1.x)"


class AnswerChain:
    """A reusable chain over the answer prompt, built with LCEL."""

    def __init__(self, llm, prompt):
        self.llm = llm
        self.prompt = prompt
        self.pipeline = prompt | llm | StrOutputParser()

    def run(self, **kwargs) -> str:
        return self.pipeline.invoke(kwargs)

    def invoke(self, inputs: dict) -> dict:
        return {"text": self.pipeline.invoke(inputs)}

    def stream(self, inputs: dict):
        yield from self.pipeline.stream(inputs)


def build_llm(
    model_name: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    streaming: bool = False,
    api_key: str = "",
    long_output: bool = False,
) -> ChatOpenAI:
    """Create the chat model.

    A key typed into the sidebar wins over the one in .env / secrets, so a
    public deployment never spends the owner's credits.
    """
    key = (api_key or "").strip() or OPENAI_API_KEY
    kwargs: dict = {
        "model": model_name,
        "streaming": streaming,
        "api_key": key,
        "timeout": 90,
        "max_retries": 2,
    }
    # Reasoning models reject temperature and the penalty knobs — only send
    # them to the model families that accept them.
    if supports_temperature(model_name):
        kwargs["temperature"] = temperature
        kwargs["frequency_penalty"] = FREQUENCY_PENALTY
        kwargs["presence_penalty"] = PRESENCE_PENALTY
        # A ceiling so a runaway loop cannot bill forever — but a generous one.
        # Writing a whole game or app needs room; too small a cap truncates the
        # file mid-function, which reads as broken logic rather than a cut-off.
        kwargs["max_tokens"] = (
            GENERATE_OUTPUT_TOKENS if long_output else MAX_OUTPUT_TOKENS
        )
    return ChatOpenAI(**kwargs)


def build_answer_chain(llm) -> AnswerChain:
    """A reusable chain over the single-string answer prompt."""
    return AnswerChain(llm=llm, prompt=ANSWER_PROMPT)


def to_langchain_history(messages: list[dict], limit: int = 8):
    """Convert stored chat turns into LangChain message objects.

    Only the last `limit` turns are kept so long sessions stay cheap.
    """
    history = []
    for msg in messages[-limit:]:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        else:
            history.append(AIMessage(content=msg["content"]))
    return history


def attach_images(messages: list, images: list[dict]) -> list:
    """Rebuild the final human turn as a multimodal message.

    The prompt template only produces text, so when the user uploads
    screenshots we swap the last message's string content for a list of
    content blocks: the original text first, then each image.
    """
    if not images:
        return messages

    from .utils import image_blocks

    last = messages[-1]
    text = last.content if isinstance(last.content, str) else str(last.content)
    blocks = [{"type": "text", "text": text}] + image_blocks(images)
    return messages[:-1] + [HumanMessage(content=blocks)]


def stream_answer(
    llm, inputs: dict, history: list, images: list[dict] | None = None
) -> Iterator[str]:
    """Yield the assistant's reply chunk by chunk for st.write_stream()."""
    messages = ANSWER_CHAT_TEMPLATE.format_messages(history=history, **inputs)
    messages = attach_images(messages, images or [])

    from .utils import find_repetition

    seen: list[str] = []
    checked_at = 0

    for chunk in llm.stream(messages):
        if not chunk.content:
            continue

        # Multimodal models can emit list-shaped chunks; flatten to text.
        if isinstance(chunk.content, str):
            piece = chunk.content
        else:
            piece = "".join(
                part.get("text", "")
                for part in chunk.content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        if not piece:
            continue

        seen.append(piece)
        yield piece

        # Watch for a repetition loop and cut the stream if one starts, rather
        # than letting it run to the token limit. Checked every ~200 chars so
        # the scan costs nothing on a normal answer.
        total = sum(len(p) for p in seen)
        if total - checked_at >= 200:
            checked_at = total
            if find_repetition("".join(seen)):
                yield (
                    "\n\n---\n"
                    "⚠️ *Stopped early — the model started repeating itself. "
                    "That is a known glitch, not something wrong with your question. "
                    "Ask again, or switch model in the sidebar.*"
                )
                return


def message_role_demo(system_text: str, user_text: str, assistant_text: str) -> list:
    """Show how a conversation is represented with raw message objects."""
    return [
        SystemMessage(content=system_text),
        HumanMessage(content=user_text),
        AIMessage(content=assistant_text),
    ]
