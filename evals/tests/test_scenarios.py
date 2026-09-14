from pathlib import Path

import pytest

from horse_evals.scenarios import SCENARIO_DIR, Criterion, Scenario, load_all, load_scenario


SAMPLE = """---
title: Sample, Harness
case: sample
element: harness
prompt: harness/prompts/start-here.md
search: on
---

## The rider

You are a person. You answer briefly.

## Criteria

- first-thing: First thing that must be true.
- second-thing: Second thing that must be true.
"""


def test_load_scenario_parses_frontmatter_and_sections(tmp_path: Path):
    f = tmp_path / "sample-harness.md"
    f.write_text(SAMPLE)
    s = load_scenario(f)
    assert s == Scenario(
        slug="sample-harness",
        title="Sample, Harness",
        case="sample",
        element="harness",
        prompt="harness/prompts/start-here.md",
        search="on",
        rider="You are a person. You answer briefly.",
        criteria=[
            Criterion("first-thing", "First thing that must be true."),
            Criterion("second-thing", "Second thing that must be true."),
        ],
    )


def test_search_defaults_to_off_and_rejects_unknown(tmp_path: Path):
    f = tmp_path / "s.md"
    f.write_text(SAMPLE.replace("search: on\n", ""))
    assert load_scenario(f).search == "off"
    f.write_text(SAMPLE.replace("search: on", "search: maybe"))
    with pytest.raises(ValueError):
        load_scenario(f)


def test_criteria_bullets_need_an_id(tmp_path: Path):
    f = tmp_path / "bad.md"
    f.write_text(SAMPLE.replace("- first-thing: ", "- "))
    with pytest.raises(ValueError):
        load_scenario(f)


def test_missing_criteria_section_raises(tmp_path: Path):
    f = tmp_path / "bad.md"
    f.write_text("---\ntitle: t\ncase: c\nelement: harness\nprompt: p\n---\n\n## The rider\n\nx\n")
    with pytest.raises(ValueError):
        load_scenario(f)


def test_load_all_reads_the_real_scenarios():
    scenarios = load_all(SCENARIO_DIR)
    slugs = [s.slug for s in scenarios]
    assert "financial-model-harness" in slugs
    fm = next(s for s in scenarios if s.slug == "financial-model-harness")
    assert fm.element == "harness"
    assert fm.search == "both"
    assert fm.prompt == "harness/prompts/start-here.md"
    assert [c.id for c in fm.criteria] == [
        "asks-daily-tools",
        "surfaces-no-excel",
        "names-spreadsheet-tool",
        "learn-or-get-done",
        "one-question-per-turn",
        "setup-note-delivered",
    ]
    assert "You do not know Excel" in fm.rider
