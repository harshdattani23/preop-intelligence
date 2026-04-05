"""PreOp Intelligence MCP Server — Clinical Risk Toolkit for perioperative assessment."""

from __future__ import annotations

from src.mcp_server.app import mcp  # noqa: F401

# Import tools to register them with the mcp instance
import src.mcp_server.tools.patient_summary  # noqa: F401
import src.mcp_server.tools.surgical_risk  # noqa: F401
import src.mcp_server.tools.periop_medications  # noqa: F401
import src.mcp_server.tools.lab_readiness  # noqa: F401
import src.mcp_server.tools.anesthesia  # noqa: F401


def main():
    import os
    port = int(os.getenv("PORT", "8080"))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
