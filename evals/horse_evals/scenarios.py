"""Loads scenario files: frontmatter, a rider description, and a list of id'd yes/no criteria."""

import re
from dataclasses import dataclass
from pathlib import Path

SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

RIDER_HEADING = "## The rider"
CRITERIA_HEADING = "## Criteria"
REQUIRED_KEYS = ("title", "case", "element", "prompt")
SEARCH_VALUES = ("on", "off", "both")
CRITERION_RE = re.compile(r"^- ([a-z0-9-]+): (.+)$")


@dataclass(frozen=True)
class Criterion:
    id: str
    text: str


@dataclass(frozen=True)
class Scenario:
    slug: str
    title: str
    case: str
    element: str
    prompt: str
    search: str
    rider: str
    criteria: list[Criterion]


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise ValueError("scenario must start with frontmatter")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("unterminated frontmatter")
    data: dict[str, str] = {}
    for line in text[3:end].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.split("#", 1)[0].strip().strip("\"'")
    return data, text[end + 4:]


def _section(body: str, heading: str, next_heading: str | None) -> str:
    start = body.find(heading)
    if start == -1:
        raise ValueError(f"scenario has no '{heading}' section")
    start += len(heading)
    stop = body.find(next_heading, start) if next_heading else -1
    return body[start: stop if stop != -1 else None].strip()


def _parse_criteria(text: str, path: Path) -> list[Criterion]:
    criteria: list[Criterion] = []
    for line in text.splitlines():
        if not line.startswith("- "):
            continue
        m = CRITERION_RE.match(line.strip())
        if not m:
            raise ValueError(f"{path}: criterion bullet must look like '- some-id: statement', got {line!r}")
        criteria.append(Criterion(m.group(1), m.group(2).strip()))
    if not criteria:
        raise ValueError(f"{path} has no criteria bullets")
    ids = [c.id for c in criteria]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path} has duplicate criterion ids")
    return criteria


def load_scenario(path: Path) -> Scenario:
    data, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"{path} frontmatter missing {missing}")
    search = data.get("search", "off")
    if search not in SEARCH_VALUES:
        raise ValueError(f"{path}: search must be one of {SEARCH_VALUES}, got {search!r}")
    rider = _section(body, RIDER_HEADING, CRITERIA_HEADING)
    criteria = _parse_criteria(_section(body, CRITERIA_HEADING, None), path)
    return Scenario(
        slug=path.stem,
        title=data["title"],
        case=data["case"],
        element=data["element"],
        prompt=data["prompt"],
        search=search,
        rider=rider,
        criteria=criteria,
    )


def load_all(directory: Path = SCENARIO_DIR) -> list[Scenario]:
    return [load_scenario(p) for p in sorted(directory.glob("*.md"))]
