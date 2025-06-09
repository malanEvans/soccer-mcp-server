import asyncio

from src.server_config import ServerConfig
from src.tools_helper import SoccerMCPToolsHelper

server_config = ServerConfig()

mcp_tool_helper = SoccerMCPToolsHelper(
    server_config=server_config,
)


def get_competition_info(competition_name: str) -> str:
    """
    Get competition information by competition name.
    Competition name could be cup name, league name, etc.

    Args:
        competition_name: Name of the competition to look up

    Returns:
        str: Competition information including name, type, current season, and previous seasons
             or error message if competition is not supported
    """

    competition_info_list = asyncio.run(
        mcp_tool_helper.get_competition_info(competition_name)
    )

    if not competition_info_list:
        available_competitions = asyncio.run(
            mcp_tool_helper.get_supported_competitions()
        )
        return f"""
        Information not found for {competition_name}.
        It might be because the competition is not supported.
        Please try again or try a different competition.
        Available competitions: {', '.join(available_competitions)}
        """

    response = ""
    for comp in competition_info_list:
        response += f"Name: {comp.name}\n"
        response += f"Type: {comp.type}\n"
        current_season = comp.current_season
        if current_season:
            response += "\nCurrent Season:\n"
            response += f"  Start: {current_season.start_date}\n"
            response += f"  End: {current_season.end_date}\n"
            response += f"  Current Matchday: {current_season.current_match_date}\n"
            if current_season.winner:
                response += f"  Winner: {current_season.winner.name}\n"
        if comp.seasons:
            response += f"\nPrevious Seasons:\n {', '.join([season.model_dump_json() for season in comp.seasons])}"
        response += "\n" + "=" * 50 + "\n"
    return response
