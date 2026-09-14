"""CLI: build the scenario dataset in Phoenix and run one experiment per model under test.

Usage, from inside evals/ with the Phoenix server already running:
    uv run python -m horse_evals.run                          # all scenarios, all models in config
    uv run python -m horse_evals.run --model openai/gpt-5.6-sol
    uv run python -m horse_evals.run --scenario financial-model-harness
    uv run python -m horse_evals.run --repetitions 1
    uv run python -m horse_evals.run --dry-run                # one interview, printed, no Phoenix
"""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from typing import Any, Callable

from horse_evals import config
from horse_evals.interview import run_interview
from horse_evals.judges import build_evaluators, format_transcript, judge_criterion
from horse_evals.prompts import content_hash, read_prompt
from horse_evals.scenarios import Scenario, load_all

SEARCH_MODES = {"off": [False], "on": [True], "both": [False, True]}


def build_rows(scenarios: list[Scenario]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for s in scenarios:
        for search in SEARCH_MODES[s.search]:
            rows.append({
                "input": {"scenario": s.slug, "search": search, "prompt_path": s.prompt, "rider": s.rider},
                "output": {"criteria": [{"id": c.id, "text": c.text} for c in s.criteria]},
                "metadata": {"title": s.title, "case": s.case, "element": s.element, "search": search},
            })
    return rows


def dataset_name(rows: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return f"horse-scenarios-{digest[:8]}"


def snapshot_prompts(scenarios: list[Scenario]) -> dict[str, str]:
    return {path: read_prompt(config.REPO_ROOT / path) for path in sorted({s.prompt for s in scenarios})}


def make_task(
    client: Any,
    model_under_test: str,
    prompts: dict[str, str],
    max_turns: int,
    max_tokens: dict[str, int],
    search_tool: dict[str, Any],
) -> Callable[..., dict[str, Any]]:
    def task(input: dict[str, Any]) -> dict[str, Any]:
        result = run_interview(
            client,
            prompt_text=prompts[input["prompt_path"]],
            rider_text=input["rider"],
            model_under_test=model_under_test,
            rider_model=config.RIDER_MODEL,
            max_turns=max_turns,
            search_tool=search_tool if input.get("search") else None,
            max_tokens=max_tokens,
        )
        return {**result, "model": model_under_test}

    return task


def git_provenance(paths: list[str]) -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=config.REPO_ROOT, text=True).strip()

    try:
        return {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain", "--", *paths))}
    except Exception:
        return {"commit": "unknown", "dirty": False}


def _error_of(run: Any) -> Any:
    return run.get("error") if isinstance(run, dict) else getattr(run, "error", None)


def summarize(result: dict[str, Any]) -> dict[str, int]:
    task_runs = list(result.get("task_runs", []))
    evaluation_runs = list(result.get("evaluation_runs", []))
    return {
        "task_runs": len(task_runs),
        "task_errors": sum(1 for r in task_runs if _error_of(r)),
        "evaluation_runs": len(evaluation_runs),
        "evaluation_errors": sum(1 for r in evaluation_runs if _error_of(r)),
    }


def _openrouter_client() -> Any:
    from openai import OpenAI

    if not config.OPENROUTER_API_KEY:
        raise SystemExit("OPENROUTER_API_KEY is not set. Put it in a .env file at the repo root.")
    return OpenAI(
        base_url=config.OPENROUTER_BASE_URL,
        api_key=config.OPENROUTER_API_KEY,
        timeout=config.REQUEST_TIMEOUT_SECONDS,
        max_retries=config.CLIENT_MAX_RETRIES,
    )


def _get_or_create_dataset(px: Any, rows: list[dict[str, Any]]) -> Any:
    name = dataset_name(rows)
    if any(d["name"] == name for d in px.datasets.list()):
        return px.datasets.get_dataset(dataset=name)
    return px.datasets.create_dataset(name=name, examples=rows, dataset_description=f"{len(rows)} HORSE scenario rows")


def _dry_run(client: Any, rows: list[dict[str, Any]], prompts: dict[str, str], model: str) -> None:
    row = rows[0]
    print(f"--- dry run: {row['input']['scenario']} search={row['input']['search']} model={model}")
    task = make_task(client, model, prompts, config.MAX_TURNS, config.MAX_TOKENS, config.SEARCH_TOOL)
    output = task(input=row["input"])
    print(format_transcript(output["transcript"]))
    print(f"\n--- status={output['status']} turns={output['turns']}")
    transcript_text = format_transcript(output["transcript"])
    for c in row["output"]["criteria"]:
        v = judge_criterion(client, config.JUDGE_MODEL, transcript_text, output["note"], c["text"], max_tokens=config.MAX_TOKENS["judge"])
        print(f"{c['id']}: {v['verdict']}. {v['reason']}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run HORSE prompt evals into Phoenix.")
    parser.add_argument("--model", action="append", help="model under test (repeatable); default: config.MODELS_UNDER_TEST")
    parser.add_argument("--scenario", action="append", help="scenario slug (repeatable); default: all")
    parser.add_argument("--repetitions", type=int, default=config.REPETITIONS, help=f"runs per row (default {config.REPETITIONS})")
    parser.add_argument("--dry-run", action="store_true", help="run one interview for the first row, print it, contact nothing but OpenRouter")
    args = parser.parse_args(argv)

    scenarios = load_all()
    if args.scenario:
        scenarios = [s for s in scenarios if s.slug in set(args.scenario)]
        if not scenarios:
            raise SystemExit(f"no scenarios matched {args.scenario}")
    rows = build_rows(scenarios)
    prompts = snapshot_prompts(scenarios)
    models = args.model or config.MODELS_UNDER_TEST
    client = _openrouter_client()

    if args.dry_run:
        _dry_run(client, rows, prompts, models[0])
        return

    from phoenix.client import Client
    from phoenix.otel import register

    register(project_name=config.PHOENIX_PROJECT, auto_instrument=True, verbose=False)
    px = Client()
    dataset = _get_or_create_dataset(px, rows)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    provenance = git_provenance(sorted({s.prompt for s in scenarios}))
    evaluators = build_evaluators(client, config.JUDGE_MODEL, scenarios, max_tokens=config.MAX_TOKENS["judge"])

    for model in models:
        print(f"\n=== {model} on {dataset.name}, {args.repetitions} repetition(s) ===")
        result = px.experiments.run_experiment(
            dataset=dataset,
            task=make_task(client, model, prompts, config.MAX_TURNS, config.MAX_TOKENS, config.SEARCH_TOOL),
            evaluators=evaluators,
            experiment_name=f"{model.replace('/', '_')}-{stamp}",
            experiment_metadata={
                "model_under_test": model,
                "rider_model": config.RIDER_MODEL,
                "judge_model": config.JUDGE_MODEL,
                "repetitions": args.repetitions,
                "max_turns": config.MAX_TURNS,
                "prompts_commit": provenance["commit"],
                "prompts_dirty": provenance["dirty"],
                "prompt_hashes": {path: content_hash(text) for path, text in prompts.items()},
            },
            repetitions=args.repetitions,
            retries=0,
            timeout=900,  # Phoenix client's HTTP timeout per call, not a cap on task execution time.
        )
        print(json.dumps(summarize(result)))


if __name__ == "__main__":
    main()
