from __future__ import annotations

import sys
from pathlib import Path

from mcp.client.stdio import StdioServerParameters

from app.core.config import settings


def get_arxiv_mcp_server_params() -> StdioServerParameters:
    command = settings.arxiv_mcp_command or sys.executable
    storage_path = Path(settings.arxiv_mcp_storage_path).resolve()
    storage_path.mkdir(parents=True, exist_ok=True)

    return StdioServerParameters(
        command=command,
        args=["-m", settings.arxiv_mcp_module, "--storage-path", str(storage_path)],
    )
