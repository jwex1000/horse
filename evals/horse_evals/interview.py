"""The interview loop: the prompt under test talks to a simulated rider until the note is delivered."""

from typing import Any

DONE_MARKER = "[DONE]"

RIDER_RULES = f"""You are playing a person who is talking to an AI assistant. Stay in character as the person described below for the whole conversation.

Rules:
- Reply as this person would, in their voice, one reply per message.
- Answer only what was asked. Do not volunteer information the assistant did not ask for.
- Push back where this person would push back.
- If the assistant presents a recommendation or a draft and asks whether it is right, judge it as this person would. If it is acceptable, say so.
- Once the assistant has written the final note and stopped, reply with exactly {DONE_MARKER} and nothing else.

The person:
"""


def _as_dict(annotation: Any) -> dict[str, Any]:
    if hasattr(annotation, "model_dump"):
        return annotation.model_dump()
    return dict(annotation)


def chat(
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    kwargs: dict[str, Any] = {"model": model, "messages": messages}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if tools:
        # OpenRouter server tools are not in the OpenAI client's tool types, so they go in the raw body.
        kwargs["extra_body"] = {"tools": tools}
    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message
    content = message.content or ""
    citations = [_as_dict(a) for a in (getattr(message, "annotations", None) or [])]
    return content, citations


def run_interview(
    client: Any,
    prompt_text: str,
    rider_text: str,
    model_under_test: str,
    rider_model: str,
    max_turns: int,
    *,
    search_tool: dict[str, Any] | None = None,
    max_tokens: dict[str, int] | None = None,
) -> dict[str, Any]:
    caps = max_tokens or {}
    tools = [search_tool] if search_tool else None
    # The conversation as the model under test sees it: the prompt is what a person pastes in.
    under_test_messages: list[dict[str, str]] = [{"role": "user", "content": prompt_text}]
    # The conversation as the rider sees it: the assistant's messages arrive as "user" turns.
    rider_messages: list[dict[str, str]] = [{"role": "system", "content": RIDER_RULES + rider_text}]
    transcript: list[dict[str, Any]] = []

    def finish(status: str, turns: int) -> dict[str, Any]:
        note = next(m["content"] for m in reversed(transcript) if m["role"] == "assistant")
        return {"transcript": transcript, "note": note, "turns": turns, "status": status, "search": bool(search_tool)}

    for turn in range(1, max_turns + 1):
        assistant, citations = chat(
            client, model_under_test, under_test_messages, tools=tools, max_tokens=caps.get("under_test")
        )
        entry: dict[str, Any] = {"role": "assistant", "content": assistant}
        if citations:
            entry["citations"] = citations
        transcript.append(entry)
        under_test_messages.append({"role": "assistant", "content": assistant})
        rider_messages.append({"role": "user", "content": assistant})

        rider, _ = chat(client, rider_model, rider_messages, max_tokens=caps.get("rider"))
        if rider.strip() == DONE_MARKER:
            return finish("completed", turn)
        transcript.append({"role": "rider", "content": rider})
        rider_messages.append({"role": "assistant", "content": rider})
        under_test_messages.append({"role": "user", "content": rider})

    return finish("capped", max_turns)
