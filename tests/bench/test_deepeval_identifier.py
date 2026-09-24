"""Tests for auto-generated DeepEval run identifiers."""

from bench_eval.results import default_deepeval_identifier


def test_default_deepeval_identifier_bench_browser_use():
    assert default_deepeval_identifier("bench", "browser-use", "gpt-4.1-mini") == (
        "bench-browser-use-gpt-4.1-mini"
    )


def test_default_deepeval_identifier_openrouter_model():
    assert default_deepeval_identifier(
        "bench",
        "hermes-ouroboros",
        "google/gemini-2.5-flash",
    ) == "bench-hermes-ouroboros-google_gemini-2.5-flash"


def test_default_deepeval_identifier_ouroboros_harness_alias():
    assert default_deepeval_identifier("bench", "ouroboros_cut", "gpt-4.1-mini") == (
        "bench-ouroboros-cut-gpt-4.1-mini"
    )
