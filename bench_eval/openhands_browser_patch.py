"""Runtime patches for OpenHands browser-use integration in WebPageBench evals."""

from __future__ import annotations

import atexit
import json
import os
import threading
from typing import Any

_PORTAL_CLOSE_TIMEOUT_SECONDS = 5.0
_SHUTDOWN_ATEXIT_REGISTERED = False


def is_openhands_browser_executor_alive(executor: Any | None) -> bool:
    """Return True when a shared BrowserToolExecutor can still run browser actions."""
    if executor is None:
        return False
    if getattr(executor, "_cleanup_initiated", False):
        return False
    async_executor = getattr(executor, "_async_executor", None)
    if async_executor is None:
        return False
    return getattr(async_executor, "_portal", None) is not None


def _take_openhands_shared_executor() -> Any | None:
    try:
        from openhands.tools.browser_use.definition import BrowserToolSet
    except ImportError:
        return None

    with BrowserToolSet._shared_executor_lock:
        executor = BrowserToolSet._shared_executor
        BrowserToolSet._shared_executor = None
    return executor


def discard_openhands_browser_executor(*, reason: str = "") -> None:
    """Drop the shared executor without waiting on the anyio portal join."""
    executor = _take_openhands_shared_executor()
    if executor is None:
        return
    setattr(executor, "_cleanup_initiated", True)
    async_executor = getattr(executor, "_async_executor", None)
    close_async = getattr(async_executor, "close", None)

    def _close() -> None:
        try:
            if callable(close_async):
                close_async()
        except Exception as exc:
            prefix = (
                f"[openhands] browser executor cleanup ({reason})"
                if reason
                else "[openhands] browser executor cleanup"
            )
            print(f"{prefix} warning: {exc}", flush=True)

    thread = threading.Thread(
        target=_close, name="dab-openhands-executor-close", daemon=True
    )
    thread.start()
    thread.join(_PORTAL_CLOSE_TIMEOUT_SECONDS)


def ensure_openhands_browser_executor_ready() -> None:
    """Drop the shared executor only when its browser session is dead.

    OpenHands keeps one BrowserToolExecutor per process. ``conversation.close()``
    with ``delete_on_close=True`` stops Chromium but leaves the dead executor
    registered, so the next benchmark task fails with "No browser session active".
    When the executor is still alive we keep it so the next task can reuse Chromium.
    """
    try:
        from openhands.tools.browser_use.definition import BrowserToolSet
    except ImportError:
        return

    with BrowserToolSet._shared_executor_lock:
        executor = BrowserToolSet._shared_executor

    if executor is None or is_openhands_browser_executor_alive(executor):
        return

    discard_openhands_browser_executor(reason="stale session")


def reset_openhands_browser_executor() -> None:
    """Force-close and clear the shared executor (tests and emergency cleanup)."""
    discard_openhands_browser_executor()


def shutdown_openhands_runtime() -> None:
    """Close Chromium/portal before interpreter atexit so pytest can exit."""
    discard_openhands_browser_executor(reason="process exit")


def _register_openhands_shutdown_atexit() -> None:
    global _SHUTDOWN_ATEXIT_REGISTERED
    if _SHUTDOWN_ATEXIT_REGISTERED:
        return
    atexit.register(shutdown_openhands_runtime)
    _SHUTDOWN_ATEXIT_REGISTERED = True


def apply_openhands_async_executor_patch() -> None:
    """Avoid a hang on anyio BlockingPortal.join after a finished eval.

    OpenHands registers AsyncExecutor.close at atexit. The portal thread is
    non-daemon and waits on Chromium, so pytest sits after "Evaluation completed".
    """
    try:
        from anyio.from_thread import start_blocking_portal
        from openhands.sdk.utils.async_executor import AsyncExecutor
    except ImportError:
        return

    if getattr(AsyncExecutor, "_dab_close_patched", False):
        _register_openhands_shutdown_atexit()
        return

    def _ensure_portal(self: Any):
        with self._lock:
            if self._portal is None:
                orig_thread = threading.Thread

                class DaemonThread(orig_thread):
                    def __init__(self, *args: Any, **kwargs: Any):
                        kwargs["daemon"] = True
                        super().__init__(*args, **kwargs)

                threading.Thread = DaemonThread  # type: ignore[misc]
                try:
                    self._portal_cm = start_blocking_portal()
                    self._portal = self._portal_cm.__enter__()
                finally:
                    threading.Thread = orig_thread
                self._atexit_registered = True
            return self._portal

    def close(self: Any) -> None:
        with self._lock:
            portal = self._portal
            self._portal_cm = None
            self._portal = None
        if portal is None:
            return

        def _stop() -> None:
            try:
                stop = getattr(portal, "stop", None)
                if callable(stop):
                    portal.call(stop, True)
            except Exception:
                pass

        thread = threading.Thread(
            target=_stop, name="dab-openhands-portal-stop", daemon=True
        )
        thread.start()
        thread.join(_PORTAL_CLOSE_TIMEOUT_SECONDS)
        if thread.is_alive():
            print(
                "[openhands] AsyncExecutor portal stop timed out; "
                "continuing process shutdown",
                flush=True,
            )

    AsyncExecutor._ensure_portal = _ensure_portal
    AsyncExecutor.close = close
    AsyncExecutor._dab_close_patched = True
    _register_openhands_shutdown_atexit()


def ensure_mcp_identity_assertion_params() -> None:
    from bench_eval.mcp_compat import apply_mcp_fastmcp_bridge

    apply_mcp_fastmcp_bridge()


def prepare_openhands_runtime() -> None:
    """Make OpenHands importable and prevent post-eval portal hangs."""
    ensure_mcp_identity_assertion_params()
    apply_openhands_mcp_server_patch()
    apply_openhands_async_executor_patch()
    apply_openhands_browser_executor_close_patch()


def apply_openhands_mcp_server_patch() -> None:
    """Skip browser-use MCP handler registration (OpenHands does not serve MCP).

    The shared eval venv keeps mcp 1.26.0 for browser-use / ouroboros /
    langchain-mcp-adapters. If mcp 2.x is present, ``Server.list_tools`` is gone
    and ``BrowserUseServer.__init__`` crashes; this no-op is safe on both majors.
    """
    from browser_use.mcp.server import BrowserUseServer

    if getattr(BrowserUseServer, "_dab_skip_mcp_handlers", False):
        return

    def _setup_handlers(self: Any) -> None:
        return None

    BrowserUseServer._setup_handlers = _setup_handlers
    BrowserUseServer._dab_skip_mcp_handlers = True


def apply_openhands_browser_executor_close_patch() -> None:
    """Do not wait on BrowserToolExecutor.close() during interpreter shutdown."""
    try:
        from openhands.tools.browser_use import impl
    except ImportError:
        return
    if getattr(impl.BrowserToolExecutor, "_dab_close_patched", False):
        return

    def close(self: Any) -> None:
        if getattr(self, "_cleanup_initiated", False):
            return
        self._cleanup_initiated = True
        try:
            from openhands.tools.browser_use.definition import BrowserToolSet

            with BrowserToolSet._shared_executor_lock:
                if BrowserToolSet._shared_executor is self:
                    BrowserToolSet._shared_executor = None
        except Exception:
            pass
        async_executor = getattr(self, "_async_executor", None)
        close_async = getattr(async_executor, "close", None)
        if not callable(close_async):
            return
        thread = threading.Thread(
            target=close_async, name="dab-openhands-executor-close", daemon=True
        )
        thread.start()
        thread.join(_PORTAL_CLOSE_TIMEOUT_SECONDS)

    impl.BrowserToolExecutor.close = close
    impl.BrowserToolExecutor._dab_close_patched = True


def force_exit_openhands_eval(exitstatus: int | object = 0) -> None:
    """End the pytest process after OpenHands eval so anyio join cannot hang it.

    DeepEval has already printed results and ``eval_run_recorder`` has written
    ``results.json``. Full-bench runs can otherwise sit until wall-timeout.
    """
    from bench_eval.harness_names import normalize_harness_name

    try:
        harness = normalize_harness_name(os.getenv("AGENT_HARNESS", ""))
    except Exception:
        harness = str(os.getenv("AGENT_HARNESS") or "")
    if harness != "openhands":
        return
    try:
        _take_openhands_shared_executor()
    except Exception:
        pass
    _kill_chromium_children()
    try:
        code = int(exitstatus)
    except (TypeError, ValueError):
        code = 1
    print(f"[openhands] forcing process exit ({code}) after eval", flush=True)
    os._exit(code)


def _kill_chromium_children() -> None:
    try:
        import psutil
    except Exception:
        return
    try:
        parent = psutil.Process()
        children = parent.children(recursive=True)
    except Exception:
        return
    for child in children:
        try:
            name = (child.name() or "").lower()
            if "chrom" in name:
                child.kill()
        except Exception:
            continue


def apply_openhands_browser_get_state_patch() -> None:
    """Unpack (state_json, screenshot) tuples returned by browser-use."""
    from openhands.tools.browser_use import impl

    if getattr(impl.BrowserToolExecutor, "_dab_get_state_patched", False):
        return

    async def get_state(self: Any, include_screenshot: bool = False):
        from openhands.tools.browser_use.definition import BrowserObservation

        await self._ensure_initialized()
        state_json, screenshot_data = await self._server._get_browser_state(
            include_screenshot
        )

        if include_screenshot and screenshot_data:
            try:
                result_data = json.loads(state_json)
                result_data.pop("screenshot", None)
                state_json = json.dumps(result_data, indent=2)
            except json.JSONDecodeError:
                pass

        return BrowserObservation.from_text(
            text=state_json,
            is_error=False,
            screenshot_data=screenshot_data if include_screenshot else None,
            full_output_save_dir=self.full_output_save_dir,
        )

    impl.BrowserToolExecutor.get_state = get_state
    impl.BrowserToolExecutor._dab_get_state_patched = True
