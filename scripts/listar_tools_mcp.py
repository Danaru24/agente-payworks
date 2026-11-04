"""Imprime las tools que expone el MCP de Grafana y sus argumentos.
Úsalo para confirmar los nombres de argumentos en tools/grafana_mcp.py.
    python scripts/listar_tools_mcp.py
"""
import asyncio
import json
import os
 
from langchain_mcp_adapters.client import MultiServerMCPClient
 
 
async def main():
    token = os.getenv("MCP_GRAFANA_TOKEN", "")
    cliente = MultiServerMCPClient({"grafana": {
        "transport": "streamable_http", "url": os.environ["MCP_GRAFANA_URL"],
        "headers": {"Authorization": f"Bearer {token}"} if token else {}}})
    for t in await cliente.get_tools():
        esquema = t.args_schema if isinstance(t.args_schema, dict) else t.args_schema.model_json_schema()
        print(f"\n## {t.name}\n{t.description}\n{json.dumps(esquema.get('properties', {}), indent=2)}")
 
 
asyncio.run(main())