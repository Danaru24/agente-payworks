"""Imprime las tools que expone el MCP de Grafana y sus argumentos.
Úsalo para confirmar los nombres de argumentos en tools/grafana_mcp.py.
    python scripts/listar_tools_mcp.py

Lee MCP_GRAFANA_URL (obligatoria) y MCP_GRAFANA_TOKEN (opcional, Bearer) del
entorno o del `.env` en la raíz del repo.
"""
import asyncio
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)


async def main():
    url = os.getenv("MCP_GRAFANA_URL", "").strip()
    if not url:
        raise RuntimeError(f"Falta MCP_GRAFANA_URL en el entorno o en {ENV_PATH}")
    token = os.getenv("MCP_GRAFANA_TOKEN", "").strip()  # opcional; nunca se imprime
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    timeout = float(os.getenv("MCP_TIMEOUT_S", "30"))
    async with httpx.AsyncClient(headers=headers, timeout=timeout) as http_client:
        async with streamable_http_client(url, http_client=http_client) as (
            read_stream, write_stream, _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                respuesta = await session.list_tools()
                for t in respuesta.tools:
                    esquema = t.inputSchema or {}
                    print(f"\n## {t.name}\n{t.description}\nrequired: {esquema.get('required', [])}"
                          f"\n{json.dumps(esquema.get('properties', {}), indent=2, ensure_ascii=False)}")


asyncio.run(main())
