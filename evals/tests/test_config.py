from horse_evals import config


def test_repo_root_is_the_horse_repo():
    assert (config.REPO_ROOT / "harness" / "prompts" / "start-here.md").exists()


def test_openrouter_base_url():
    assert config.OPENROUTER_BASE_URL == "https://openrouter.ai/api/v1"


def test_models_under_test_is_a_nonempty_list():
    assert isinstance(config.MODELS_UNDER_TEST, list)
    assert config.MODELS_UNDER_TEST


def test_limits_and_search_tool():
    assert config.REPETITIONS >= 1
    assert config.REQUEST_TIMEOUT_SECONDS > 0
    assert set(config.MAX_TOKENS) == {"under_test", "rider", "judge"}
    assert config.SEARCH_TOOL == {"type": "openrouter:web_search"}
