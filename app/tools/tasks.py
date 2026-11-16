from fastmcp import FastMCP

from app.api_client import get_client


def register_task_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_task_details(task_id: str) -> dict:
        async with get_client() as client:
            response = await client.get("/actions/api/task", params={"taskId": task_id})
            response.raise_for_status()
            return response.json()

    @mcp.tool()
    async def get_task_status(task_id: str) -> dict:
        async with get_client() as client:
            response = await client.get("/post-task-processing/status", params={"taskId": task_id})
            response.raise_for_status()
            return response.json()

    @mcp.tool()
    async def trigger_task_processing(task_id: str, actions: list[str], sync: bool = False) -> dict:
        async with get_client() as client:
            response = await client.post(
                "/post-task-processing",
                params={"sync": sync},
                json={"taskId": task_id, "actions": actions},
            )
            response.raise_for_status()
            return response.json()
