from types import SimpleNamespace

from horse_evals.interview import DONE_MARKER, run_interview


class FakeClient:
    """Scripted stand-in for the OpenAI client. Replies are keyed by model and consumed in order."""

    def __init__(self, replies: dict[str, list]):
        self.replies = {m: list(r) for m, r in replies.items()}
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append({k: (list(v) if k == "messages" else v) for k, v in kwargs.items()})
        reply = self.replies[kwargs["model"]].pop(0)
        content, annotations = reply if isinstance(reply, tuple) else (reply, None)
        message = SimpleNamespace(content=content, annotations=annotations)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


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
