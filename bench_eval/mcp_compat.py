"""Shared-venv bridge: mcp 1.26.0 (browser-use/ouroboros) + fastmcp 3.2.0 (openhands-sdk).

openhands-sdk 1.17.0 locks fastmcp==3.2.0. Newer fastmcp 3.3+ needs mcp 2.x
IdentityAssertionParams; this module fills that symbol if a newer wheel sneaks in.
"""

from __future__ import annotations

_APPLIED = False


def apply_mcp_fastmcp_bridge() -> None:
    """Inject mcp 2-only auth symbols so fastmcp 3 can import on mcp 1.26."""
    global _APPLIED
    try:
        from mcp.server.auth import provider
    except Exception:
        return
    if getattr(provider, "IdentityAssertionParams", None) is None:
        try:
            from pydantic import BaseModel
        except Exception:
            provider.IdentityAssertionParams = type("IdentityAssertionParams", (), {})
        else:

            class IdentityAssertionParams(BaseModel):
                assertion: str = ""
                scopes: list[str] | None = None
                resource: str | None = None

            provider.IdentityAssertionParams = IdentityAssertionParams
    _APPLIED = True
