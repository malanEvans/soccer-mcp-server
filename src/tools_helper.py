"""
Soccer MCP Tools - A collection of utilities for working with football data.
"""

from typing import Any, Dict, List

from llm_utils import invoke_llm
from src.server_config import ServerConfig
from src.soccer_client import Competition, FootballDataClient


class SoccerMCPToolsHelper:
    """A collection of tools for working with football data.

    This class provides methods to interact with football data using the provided
    server configuration and football data client.
    """

    def __init__(self, server_config: ServerConfig) -> None:
        """Initialize the SoccerMCPToolsHelper with required dependencies.

        Args:
            server_config: The server configuration containing API settings
        """
        self._server_config = server_config
        self._competition_mapping = None

    async def _get_competitions_mapping(self) -> Dict[str, Any]:
        async with FootballDataClient(self._server_config) as client:
            competitions = await client.get_competitions()
        return {
            comp.name: {"id": comp.competition_id, "code": comp.code}
            for comp in competitions
        }

    async def get_supported_competitions(self) -> List[str]:
        if self._competition_mapping is None:
            self._competition_mapping = await self._get_competitions_mapping()
        return list(self._competition_mapping.keys())

    async def get_competition_info(self, competition_name: str) -> List[Competition]:
        """
        Get information about a competition by its name.

        Args:
            competition_name: The name of the competition (e.g., 'Premier League')

        Returns:
            List of Competition objects containing competition information including:
            - id: Competition ID
            - name: Competition name
            - code: Competition code
            - current_season: Current season details
        """
        if self._competition_mapping is None:
            self._competition_mapping = await self._get_competitions_mapping()

        # First try to get competition from our mapping
        competition_id_list = await invoke_llm(
            nebius_api_key=self._server_config.nebius_api_key,
            prompt_id="find-competition-id.j2",
            prompt_args={
                "competition_name": competition_name,
                "competition_mapping": self._competition_mapping,
            },
        )

        if not competition_id_list:
            return []

        competitions = []
        async with FootballDataClient(self._server_config) as client:
            for competition_id_details in competition_id_list:
                competition_info = await client.get_competition(
                    competition_id_details["id"]
                )
                competitions.append(competition_info)

        return competitions
