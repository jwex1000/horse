# HORSE evals

Runs each HORSE prompt against case-study scenarios in several models, with and without web search, with a simulated rider and one LLM judge per criterion, and records everything in a local Phoenix instance. Design notes live outside the repo.

## One-time setup

1. Install [uv](https://docs.astral.sh/uv/).
2. Create `.env` at the repo root containing `OPENROUTER_API_KEY=...`. It is git-ignored.
3. From `evals/`, run `uv sync`.

## Every session

1. Start Phoenix: `cd evals && uvx arize-phoenix serve`. UI at http://localhost:6006.
2. In another terminal, from `evals/`:
   - `uv run python -m horse_evals.run` runs every scenario in every model in `horse_evals/config.py`, three times each.
   - `--scenario <slug>` and `--model <id>` narrow it. Both repeat. `--repetitions N` changes the count.
   - `--dry-run` runs one interview for the first row, prints it with the judge's verdicts, and never contacts Phoenix.
3. Read results in Phoenix under Datasets. Each run is an experiment named by model and time. Every criterion is its own column. `n/a` means the criterion is not part of that scenario; `error` means the judge did not answer cleanly, and it is not counted as a failure. Click a row to read the transcript and the judge's reason.

## Adding a scenario

Copy `scenarios/financial-model-harness.md`, keep the frontmatter keys, describe the rider in prose, and list criteria as `- some-id: statement` bullets a judge can answer yes or no. Reuse an existing id when the statement means the same thing. `search: both` runs the scenario with and without web search. Unchanged scenarios reuse the same Phoenix dataset, so experiments stay comparable; any change to any scenario starts a new dataset.

## Tests

`uv run pytest` from `evals/`. No network or API key needed.
