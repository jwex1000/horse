from types import SimpleNamespace

from horse_evals.interview import DONE_MARKER, is_done, run_interview


class FakeClient:
    """Scripted stand-in for the OpenAI client. Replies are keyed by model and consumed in order.

    A reply is either a bare content string, or a tuple of up to
    (content, annotations, finish_reason), with trailing elements defaulting to None.
    """

    def __init__(self, replies: dict[str, list]):
        self.replies = {m: list(r) for m, r in replies.items()}
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append({k: (list(v) if k == "messages" else v) for k, v in kwargs.items()})
        reply = self.replies[kwargs["model"]].pop(0)
        if isinstance(reply, tuple):
            content, annotations, finish_reason = (list(reply) + [None, None])[:3]
        else:
            content, annotations, finish_reason = reply, None, None
        message = SimpleNamespace(content=content, annotations=annotations)
        choice = SimpleNamespace(message=message, finish_reason=finish_reason)
        return SimpleNamespace(choices=[choice])


def test_alternates_until_rider_says_done():
    client = FakeClient({
        "under-test": ["What are you about to do?", "Which tools do you have?", "Setup note: use X."],
        "rider": ["Build a model.", "Just email.", DONE_MARKER],
    })
    result = run_interview(client, "PROMPT", "RIDER", "under-test", "rider", max_turns=10)
    assert result["status"] == "completed"
    assert result["turns"] == 3
    assert result["note"] == "Setup note: use X."
    assert result["search"] is False
    assert [m["role"] for m in result["transcript"]] == ["assistant", "rider", "assistant", "rider", "assistant"]


def test_prompt_is_first_user_message_and_rider_sees_persona_as_system():
    client = FakeClient({"under-test": ["Q1", "Note"], "rider": ["A1", DONE_MARKER]})
    run_interview(client, "PROMPT", "RIDER PERSONA", "under-test", "rider", max_turns=10)
    first_under_test = client.calls[0]
    assert first_under_test["model"] == "under-test"
    assert first_under_test["messages"][0] == {"role": "user", "content": "PROMPT"}
    assert "extra_body" not in first_under_test
    first_rider = client.calls[1]
    assert first_rider["model"] == "rider"
    assert first_rider["messages"][0]["role"] == "system"
    assert "RIDER PERSONA" in first_rider["messages"][0]["content"]
    assert first_rider["messages"][1] == {"role": "user", "content": "Q1"}


def test_stops_at_max_turns_when_rider_never_finishes():
    client = FakeClient({"under-test": ["Q"] * 5, "rider": ["A"] * 5})
    result = run_interview(client, "PROMPT", "RIDER", "under-test", "rider", max_turns=3)
    assert result["status"] == "capped"
    assert result["turns"] == 3
    assert result["note"] == "Q"


def test_search_tool_goes_only_to_model_under_test_and_citations_are_kept():
    tool = {"type": "openrouter:web_search"}
    citation = SimpleNamespace(model_dump=lambda: {"url": "https://example.com"})
    client = FakeClient({"under-test": [("Q1", [citation]), "Note"], "rider": ["A1", DONE_MARKER]})
    result = run_interview(
        client, "PROMPT", "RIDER", "under-test", "rider", max_turns=5,
        search_tool=tool, max_tokens={"under_test": 100, "rider": 50},
    )
    assert result["search"] is True
    under_test_calls = [c for c in client.calls if c["model"] == "under-test"]
    rider_calls = [c for c in client.calls if c["model"] == "rider"]
    assert all(c["extra_body"] == {"tools": [tool]} for c in under_test_calls)
    assert all("extra_body" not in c for c in rider_calls)
    assert all(c["max_tokens"] == 100 for c in under_test_calls)
    assert all(c["max_tokens"] == 50 for c in rider_calls)
    assert result["transcript"][0]["citations"] == [{"url": "https://example.com"}]
    assert "citations" not in result["transcript"][2]


def test_empty_assistant_reply_ends_interview_without_reaching_rider():
    client = FakeClient({"under-test": [None], "rider": []})
    result = run_interview(client, "PROMPT", "RIDER", "under-test", "rider", max_turns=5)
    assert result["status"] == "empty"
    assert result["turns"] == 1
    assert result["note"] == ""
    assert result["transcript"] == [{"role": "assistant", "content": ""}]
    assert all(c["model"] != "rider" for c in client.calls)


def test_empty_assistant_reply_keeps_last_non_empty_note():
    client = FakeClient({"under-test": ["Real note", None], "rider": ["More please."]})
    result = run_interview(client, "PROMPT", "RIDER", "under-test", "rider", max_turns=5)
    assert result["status"] == "empty"
    assert result["turns"] == 2
    assert result["note"] == "Real note"
    rider_calls = [c for c in client.calls if c["model"] == "rider"]
    assert len(rider_calls) == 1
    assert all(m["content"] != "" for c in rider_calls for m in c["messages"] if m["role"] == "user")


def test_finish_reason_recorded_on_entry_and_output():
    client = FakeClient({"under-test": [("Setup note.", None, "length")], "rider": [DONE_MARKER]})
    result = run_interview(client, "PROMPT", "RIDER", "under-test", "rider", max_turns=5)
    assert result["transcript"][0]["finish_reason"] == "length"
    assert result["finish_reason"] == "length"


def test_finish_reason_absent_when_not_provided():
    client = FakeClient({"under-test": ["Note"], "rider": [DONE_MARKER]})
    result = run_interview(client, "PROMPT", "RIDER", "under-test", "rider", max_turns=5)
    assert "finish_reason" not in result["transcript"][0]
    assert result["finish_reason"] is None


def test_is_done_accepts_decorated_forms():
    assert is_done(DONE_MARKER)
    assert is_done("[DONE].")
    assert is_done("**[DONE]**")
    assert is_done(" [DONE]\n")
    assert is_done('"[DONE]"')
    assert is_done("[DONE]!\n")


def test_is_done_rejects_marker_with_other_words():
    assert not is_done("Thanks, [DONE]")
    assert not is_done("[DONE] see you")
    assert not is_done("done")
    assert not is_done("")


def test_done_marker_with_trailing_punctuation_ends_interview():
    client = FakeClient({"under-test": ["Q", "Note"], "rider": ["A1", "[DONE]."]})
    result = run_interview(client, "PROMPT", "RIDER", "under-test", "rider", max_turns=5)
    assert result["status"] == "completed"
    assert result["turns"] == 2
