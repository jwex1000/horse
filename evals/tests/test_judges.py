from types import SimpleNamespace

from horse_evals.judges import (
    build_evaluators,
    ends_with_question,
    format_transcript,
    judge_criterion,
    make_criterion_evaluator,
    parse_verdict,
    question_marks_per_turn,
    rider_finished,
    turns,
)
from horse_evals.scenarios import Criterion, Scenario


class FakeClient:
    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.replies.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, annotations=None))])


OUTPUT = {
    "transcript": [
        {"role": "assistant", "content": "What are you about to do?"},
        {"role": "rider", "content": "Build a model."},
        {"role": "assistant", "content": "Which tools do you have? And what's your budget?"},
        {"role": "rider", "content": "Email. No budget."},
        {"role": "assistant", "content": "Setup note: use Claude in Excel."},
    ],
    "note": "Setup note: use Claude in Excel.",
    "turns": 3,
    "status": "completed",
    "search": False,
}

CAPPED = {
    "transcript": [
        {"role": "assistant", "content": "What tools? What budget?"},
        {"role": "rider", "content": "Email."},
    ],
    "note": "What tools? What budget?",
    "turns": 1,
    "status": "capped",
    "search": False,
}

EMPTY = {
    "transcript": [
        {"role": "assistant", "content": "Q1? Q2?"},
    ],
    "note": "",
    "turns": 1,
    "status": "empty",
    "search": False,
}

EXPECTED = {"criteria": [{"id": "c1", "text": "Names a spreadsheet tool."}, {"id": "c2", "text": "Asks about budget."}]}


def test_format_transcript_labels_speakers():
    text = format_transcript(OUTPUT["transcript"])
    assert text.startswith("ASSISTANT: What are you about to do?")
    assert "RIDER: Build a model." in text


def test_parse_verdict_accepts_fenced_object_and_rejects_everything_else():
    assert parse_verdict('```json\n{"verdict": "Yes", "reason": "It names it."}\n```') == {"verdict": "yes", "reason": "It names it."}
    assert parse_verdict("[]") is None
    assert parse_verdict("null") is None
    assert parse_verdict('"yes"') is None
    assert parse_verdict('{"verdict": "maybe", "reason": "x"}') is None
    assert parse_verdict('{"verdict": "yes"}') is None
    assert parse_verdict("I cannot decide.") is None


def test_judge_criterion_uses_system_message_and_retries_once():
    client = FakeClient(["garbage", '{"verdict": "no", "reason": "Never mentioned."}'])
    result = judge_criterion(client, "judge", "T", "N", "Names a spreadsheet tool.")
    assert result == {"verdict": "no", "reason": "Never mentioned."}
    assert len(client.calls) == 2
    messages = client.calls[0]["messages"]
    assert messages[0]["role"] == "system"
    assert "evidence" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "Names a spreadsheet tool." in messages[1]["content"]
    assert "T" in messages[1]["content"] and "N" in messages[1]["content"]
    assert "extra_body" not in client.calls[0]


def test_judge_criterion_gives_up_after_two_bad_replies():
    client = FakeClient(["garbage", "more garbage"])
    result = judge_criterion(client, "judge", "T", "N", "C")
    assert result["verdict"] == "error"
    assert "more garbage" in result["reason"]


def test_criterion_evaluator_scores_verdicts_and_marks_missing_criteria_na():
    client = FakeClient(['{"verdict": "yes", "reason": "It names Claude in Excel."}'])
    c1 = make_criterion_evaluator(client, "judge", "c1")
    assert c1(output=OUTPUT, expected=EXPECTED) == {"score": 1.0, "label": "yes", "explanation": "It names Claude in Excel."}
    other = make_criterion_evaluator(client, "judge", "not-in-this-scenario")
    assert other(output=OUTPUT, expected=EXPECTED) == {"label": "n/a"}
    assert len(client.calls) == 1


def test_criterion_evaluator_reports_judge_errors_without_a_score():
    client = FakeClient(["bad", "bad"])
    c1 = make_criterion_evaluator(client, "judge", "c1")
    result = c1(output=OUTPUT, expected=EXPECTED)
    assert result["label"] == "error"
    assert "score" not in result


def test_build_evaluators_has_one_per_unique_criterion_plus_code_checks():
    s1 = Scenario("a", "A", "a", "harness", "p", "off", "r", [Criterion("shared", "x"), Criterion("only-a", "y")])
    s2 = Scenario("b", "B", "b", "role", "p", "off", "r", [Criterion("shared", "x"), Criterion("only-b", "z")])
    evaluators = build_evaluators(FakeClient([]), "judge", [s1, s2])
    assert set(evaluators) == {
        "shared", "only-a", "only-b",
        "rider_finished", "ends_with_question", "turns", "question_marks_per_turn",
    }


def test_code_checks():
    assert rider_finished(OUTPUT) is True
    assert rider_finished(CAPPED) is False
    assert ends_with_question(OUTPUT) is False
    assert ends_with_question(CAPPED) is True
    assert turns(OUTPUT) == 3.0
    completed = question_marks_per_turn(OUTPUT)
    assert completed["score"] == 0.5 and completed["label"] == "1/2"
    capped = question_marks_per_turn(CAPPED)
    assert capped["score"] == 0.0 and capped["label"] == "0/1"


def test_empty_status_is_not_completed_and_not_excluded_from_question_marks_per_turn():
    assert rider_finished(EMPTY) is False
    empty_result = question_marks_per_turn(EMPTY)
    assert empty_result["label"] == "0/1"
    assert empty_result["score"] == 0.0
