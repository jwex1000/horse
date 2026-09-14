from types import SimpleNamespace

from horse_evals.run import build_rows, dataset_name, git_provenance, make_task, snapshot_prompts, summarize
from horse_evals.scenarios import Criterion, Scenario

S_BOTH = Scenario("a-harness", "A", "a", "harness", "harness/prompts/start-here.md", "both", "You are A.", [Criterion("c1", "one"), Criterion("c2", "two")])
S_OFF = Scenario("b-role", "B", "b", "role", "role/prompts/start-here.md", "off", "You are B.", [Criterion("c3", "three")])


def test_build_rows_expands_search_both_into_two_rows():
    rows = build_rows([S_BOTH, S_OFF])
    assert len(rows) == 3
    assert rows[0] == {
        "input": {"scenario": "a-harness", "search": False, "prompt_path": "harness/prompts/start-here.md", "rider": "You are A."},
        "output": {"criteria": [{"id": "c1", "text": "one"}, {"id": "c2", "text": "two"}]},
        "metadata": {"title": "A", "case": "a", "element": "harness", "search": False},
    }
    assert rows[1]["input"]["search"] is True and rows[1]["input"]["scenario"] == "a-harness"
    assert rows[2]["input"] == {"scenario": "b-role", "search": False, "prompt_path": "role/prompts/start-here.md", "rider": "You are B."}


def test_dataset_name_is_stable_and_content_sensitive():
    rows = build_rows([S_BOTH, S_OFF])
    assert dataset_name(rows) == dataset_name(rows)
    assert dataset_name(rows).startswith("horse-scenarios-")
    changed = Scenario("a-harness", "A", "a", "harness", "harness/prompts/start-here.md", "both", "You are A.", [Criterion("c1", "one")])
    assert dataset_name(build_rows([changed, S_OFF])) != dataset_name(rows)


def test_snapshot_prompts_reads_each_prompt_once():
    snap = snapshot_prompts([S_BOTH, S_OFF, S_BOTH])
    assert set(snap) == {"harness/prompts/start-here.md", "role/prompts/start-here.md"}
    assert snap["harness/prompts/start-here.md"].startswith("By the end of this conversation")


class FakeClient:
    def __init__(self, replies: dict[str, list[str]]):
        self.replies = {m: list(r) for m, r in replies.items()}
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.replies[kwargs["model"]].pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, annotations=None))])


def test_make_task_uses_snapshot_and_row_search_flag(monkeypatch):
    from horse_evals import config

    monkeypatch.setattr(config, "RIDER_MODEL", "rider")
    client = FakeClient({"under-test": ["Q1", "Note"], "rider": ["A1", "[DONE]"]})
    prompts = {"harness/prompts/start-here.md": "SNAPSHOT PROMPT"}
    task = make_task(client, "under-test", prompts, max_turns=5, max_tokens={"under_test": 10, "rider": 5}, search_tool={"type": "t"})
    row = build_rows([S_BOTH])[1]  # the search=True row
    out = task(input=row["input"])
    assert out["model"] == "under-test"
    assert out["status"] == "completed"
    assert out["search"] is True
    assert client.calls[0]["messages"][0]["content"] == "SNAPSHOT PROMPT"
    assert client.calls[0]["extra_body"] == {"tools": [{"type": "t"}]}


def test_git_provenance_reports_commit_and_dirty_flag():
    prov = git_provenance(["harness/prompts"])
    assert len(prov["commit"]) == 40 or prov["commit"] == "unknown"
    assert isinstance(prov["dirty"], bool)


def test_summarize_counts_errors_in_dicts_and_objects():
    result = {
        "task_runs": [{"error": None}, {"error": "boom"}],
        "evaluation_runs": [SimpleNamespace(error=None), SimpleNamespace(error="bad"), SimpleNamespace(error=None)],
    }
    assert summarize(result) == {"task_runs": 2, "task_errors": 1, "evaluation_runs": 3, "evaluation_errors": 1}
