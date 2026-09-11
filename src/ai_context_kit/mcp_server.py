"""Read-only MCP surface for GitHub-published project context."""

from __future__ import annotations

import os

from .github_store import GitHubBundleStore


def _store_from_environment() -> GitHubBundleStore:
    repository = os.environ.get("AICTX_GITHUB_REPOSITORY")
    if not repository:
        raise RuntimeError("AICTX_GITHUB_REPOSITORY is required")
    return GitHubBundleStore(
        repository,
        ref=os.environ.get("AICTX_GITHUB_REF", "main"),
        base_path=os.environ.get("AICTX_GITHUB_PATH", ".ai-context"),
        token=os.environ.get("GITHUB_TOKEN"),
    )


def create_server():
    from mcp.server.mcpserver import MCPServer

    server = MCPServer(
        "ai-context-kit",
        instructions=(
            "Read only explicitly published ContextBundle v1 files. Check freshness before "
            "treating context as current; repository source files remain authoritative."
        ),
    )

    @server.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def list_projects() -> list[dict[str, object]]:
        """List projects explicitly published for remote context access."""
        return _store_from_environment().list_projects()

    @server.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def get_context(project: str) -> dict[str, object]:
        """Get the automatic, manual, and global context for one exact project name."""
        return _store_from_environment().get_context(project)

    @server.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def get_freshness(project: str) -> dict[str, object]:
        """Get export time, freshness label, and bounded observation scope for a project."""
        return _store_from_environment().get_freshness(project)

    return server


def entrypoint() -> None:
    create_server().run(
        transport="streamable-http",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        streamable_http_path="/mcp",
    )
