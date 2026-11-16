from fastmcp import FastMCP

from app.tools import register_task_tools

mcp = FastMCP(name="Gogig MCP Server")

register_task_tools(mcp)
