from fastmcp import FastMCP

from app.api_client import api_get


def register_user_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def whoami(
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """The signed-in user: who they are, how far they can see (campaigns, teamCampaigns, isAdmin), and their own submitted-work counts and rates. Call this first — it explains why any other answer is as narrow as it is."""
        return await api_get(
            "/mcp/users/me",
            {"startDate": start_date, "endDate": end_date},
        )

    @mcp.tool()
    async def list_team_members(
        gig_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """The roster under the user: everyone mapped to a campaign they lead, including people who have submitted nothing yet (zeroed counts). An admin must pass gig_id, since they lead every campaign."""
        return await api_get(
            "/mcp/users/team",
            {
                "gigId": gig_id,
                "startDate": start_date,
                "endDate": end_date,
                "page": page,
                "pageSize": page_size,
            },
        )

    @mcp.tool()
    async def search_users(q: str, page: int = 1, page_size: int = 20) -> dict:
        """Find a person by name (at least 2 characters). An admin searches every user and also matches email and phone, which are returned; everyone else searches only people they already reach."""
        return await api_get(
            "/mcp/users/search",
            {"q": q, "page": page, "pageSize": page_size},
        )

    @mcp.tool()
    async def get_user_performance(
        gig_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """How each person's submitted work came out, busiest first — whose work the user is actually reading, including people with no campaign mapping. Rates divide by each person's validated work, so check counts.validated before reading an extreme rate."""
        return await api_get(
            "/mcp/users/performance",
            {
                "gigId": gig_id,
                "startDate": start_date,
                "endDate": end_date,
                "page": page,
                "pageSize": page_size,
            },
        )

    @mcp.tool()
    async def get_user_details(
        user_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """One person's totals across the campaigns the caller may read. Omit user_id for the caller's own record, which is returned even when empty."""
        return await api_get(
            "/mcp/users/detail",
            {"userId": user_id, "startDate": start_date, "endDate": end_date},
        )
