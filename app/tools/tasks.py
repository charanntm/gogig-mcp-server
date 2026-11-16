from fastmcp import FastMCP


def register_task_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_task_details(task_id: str) -> dict:
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Task details retrieved successfully",
        }
