from fastmcp import FastMCP

from app.api_client import api_get


def register_campaign_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_my_campaigns(page: int = 1, page_size: int = 20) -> dict:
        """The campaigns the user may read — the valid values for gig_id on every other tool."""
        return await api_get("/mcp/campaigns", {"page": page, "pageSize": page_size})

    @mcp.tool()
    async def get_campaign_performance(
        gig_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Delivery and quality per campaign: flagged/warned counts plus delivery (submitted vs the campaign's target). delivery is null when the campaign has no target, and exceeds 1 on over-delivery."""
        return await api_get(
            "/mcp/campaigns/performance",
            {
                "gigId": gig_id,
                "startDate": start_date,
                "endDate": end_date,
                "page": page,
                "pageSize": page_size,
            },
        )
