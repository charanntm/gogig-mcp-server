from typing import Literal

from fastmcp import FastMCP

from app.api_client import api_get

Validation = Literal["flagged", "warned", "info", "clean", "unvalidated"]


def register_task_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_task_summary(
        gig_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """Count the signed-in user's submitted tasks: flagged (validation error), warned, info, clean and unvalidated. Rates are over validated work only and are null until something is validated. Dates are YYYY-MM-DD and bound when a task was submitted."""
        return await api_get(
            "/mcp/tasks/summary",
            {"gigId": gig_id, "startDate": start_date, "endDate": end_date},
        )

    @mcp.tool()
    async def list_tasks(
        gig_id: str | None = None,
        validation: Validation | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List the user's submitted tasks newest first, optionally filtered to one validation bucket. Paged; page_size caps at 100."""
        return await api_get(
            "/mcp/tasks/list",
            {
                "gigId": gig_id,
                "validation": validation,
                "startDate": start_date,
                "endDate": end_date,
                "page": page,
                "pageSize": page_size,
            },
        )

    @mcp.tool()
    async def get_task_details(task_id: str) -> dict:
        """One of the user's tasks in full: its validation state, every reason recorded against it, and what each detector read."""
        return await api_get("/mcp/tasks/detail", {"taskId": task_id})

    @mcp.tool()
    async def get_task_flag_reasons(
        gig_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """Why the user's work is being flagged or warned, busiest reason first. One task can carry several reasons, so the counts exceed flaggedTasksWithReason."""
        return await api_get(
            "/mcp/tasks/flagReasons",
            {"gigId": gig_id, "startDate": start_date, "endDate": end_date},
        )

