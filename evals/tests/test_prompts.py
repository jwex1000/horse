from pathlib import Path

import pytest

from horse_evals import config
from horse_evals.prompts import content_hash, read_prompt


def test_reads_text_after_the_prompt_heading(tmp_path: Path):
    f = tmp_path / "p.md"
    f.write_text("---\ntitle: x\n---\n\n## The prompt\n\nDo the thing.\n\nThen stop.\n")
    assert read_prompt(f) == "Do the thing.\n\nThen stop."


def test_raises_when_heading_missing(tmp_path: Path):
    f = tmp_path / "p.md"
    f.write_text("---\ntitle: x\n---\n\nNo heading here.\n")
    with pytest.raises(ValueError):
        read_prompt(f)


def test_reads_the_real_harness_prompt():
    text = read_prompt(config.REPO_ROOT / "harness" / "prompts" / "start-here.md")
    assert text.startswith("By the end of this conversation")
    assert "## The prompt" not in text


def test_content_hash_is_short_and_stable():
    assert content_hash("abc") == content_hash("abc")
    assert len(content_hash("abc")) == 12
    assert content_hash("abc") != content_hash("abd")
