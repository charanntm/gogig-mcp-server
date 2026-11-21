from typing import Literal

from fastmcp import FastMCP

from app.api_client import api_get, api_post

ReportType = Literal["pdf", "summary"]


def register_report_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def generate_campaign_report(
        gig_id: str,
        type: ReportType,
        start_date: str | None = None,
        end_date: str | None = None,
        validation_reason: str | None = None,
    ) -> dict:
        """Start generating a campaign report (full PDF or summary PDF) and email it to the signed-in user's own address. This is the one tool that changes anything — it queues a real job and sends a real email, nothing in gOGig is modified or deleted. Scoped to the user's own campaign role (brand, agency, or admin); refused for a plain executor. Returns a jobId — poll get_report_status with it for progress and the download link."""
        return await api_post(
            "/mcp/reports/generate",
            {
                "gigId": gig_id,
                "type": type,
                "startDate": start_date,
                "endDate": end_date,
                "validationReason": validation_reason,
            },
        )

    @mcp.tool()
    async def get_report_status(gig_id: str, type: ReportType) -> dict | None:
        """Check a report job's progress and get its download link once ready. status is null until the worker picks up the job. To retry a failed job or refresh an expired link, call generate_campaign_report again."""
        return await api_get(
            "/mcp/reports/status",
            {"gigId": gig_id, "type": type},
        )
