"""Settings for the eval runner. Secrets come from a git-ignored .env at the repo root."""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Model ids are OpenRouter ids, verified against https://openrouter.ai/api/v1/models on 2026-09-14.
# The rider and the judge never change between runs, so only the model under test varies.
RIDER_MODEL = "anthropic/claude-sonnet-5"
JUDGE_MODEL = "anthropic/claude-sonnet-5"

# Models the prompts are tested in. Add a line to add a model.
MODELS_UNDER_TEST = [
    "anthropic/claude-sonnet-5",
    "openai/gpt-5.6-sol",
]

# One interview is noisy. Every dataset row runs this many times per experiment.
REPETITIONS = 3

MAX_TURNS = 20
REQUEST_TIMEOUT_SECONDS = 120.0
CLIENT_MAX_RETRIES = 2
MAX_TOKENS = {"under_test": 3000, "rider": 600, "judge": 300}

# OpenRouter's server-side web search tool (beta). Only the model under test ever gets it.
SEARCH_TOOL = {"type": "openrouter:web_search"}

PHOENIX_PROJECT = "horse-evals"
