"""LLM agent evaluation on WebPageBench mock tasks."""

from bench_eval.mcp_compat import apply_mcp_fastmcp_bridge

apply_mcp_fastmcp_bridge()

from bench_eval.config import EvalConfig, load_config

__all__ = ["EvalConfig", "load_config", "run_golden"]


def __getattr__(name: str):
    if name == "run_golden":
        from bench_eval.runner import run_golden

        return run_golden
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
