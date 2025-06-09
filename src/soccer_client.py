"""
Football Data API client for interacting with football-data.org API.

This module provides a client class to interact with various endpoints of the
football-data.org API, handling authentication, rate limiting, and response parsing.
"""

import asyncio
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import aiohttp
from attr import field
from pydantic import BaseModel, ConfigDict, Field

from src.server_config import ServerConfig


class Team(BaseModel):
    """Represents a football team."""

    model_config = ConfigDict(populate_by_name=True)

    team_id: int = Field(alias="id")
    name: str
    short_name: str = Field(alias="shortName")
    tla: str
    crest: str
    address: Optional[str] = None
    website: Optional[str] = None
    founded: Optional[int] = None
    club_colors: Optional[str] = Field(None, alias="clubColors")
    venue: Optional[str] = None


class Score(BaseModel):
    home: int
    away: int


class ScoreDetails(BaseModel):
    winner: Optional[str] = None
    duration: Optional[str] = None
    full_time: Optional[Score] = field(default=None, alias="fullTime")
    half_time: Optional[Score] = field(default=None, alias="halfTime")


class Season(BaseModel):
    season_id: int = Field(alias="id")
    start_date: datetime = Field(alias="startDate")
    end_date: datetime = Field(alias="endDate")
    current_match_date: Optional[int] = Field(None, alias="currentMatchday")
    winner: Optional[Team] = None


class Match(BaseModel):
    """Represents a football match."""

    model_config = ConfigDict(populate_by_name=True)

    match_id: int = Field(alias="id")
    competition: Dict[str, Any]
    season: Season
    utc_date: datetime = Field(alias="utcDate")
    status: str
    matchday: Optional[int] = None
    stage: Optional[str] = None
    group: Optional[str] = None
    home_team: Team = Field(alias="homeTeam")
    away_team: Team = Field(alias="awayTeam")
    score: ScoreDetails


class Competition(BaseModel):
    """Represents a football competition."""

    model_config = ConfigDict(populate_by_name=True)

    competition_id: int = Field(alias="id")
    name: str
    code: str
    type: str
    current_season: Season = Field(alias="currentSeason")
    seasons: List[Season] = []


class FootballDataClient:
    """Client for interacting with the football-data.org API.

    This client provides methods to access various endpoints of the football-data.org API.
    It handles authentication, rate limiting, and response parsing.
    """

    def __init__(self, server_config: ServerConfig):
        """Initialize the client with an optional API key.

        Args:
            server_config: Server configuration object containing API key.
        """
        self._session = None
        self._api_key = server_config.api_access_token
        self._base_url = server_config.api_base_url

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            headers={"X-Auth-Token": self._api_key},
            timeout=aiohttp.ClientTimeout(total=30),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            endpoint: API endpoint (e.g., '/matches')
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data

        Returns:
            dict: JSON response from the API

        Raises:
            aiohttp.ClientError: If the request fails
        """
        url = f"{self._base_url}/{endpoint.lstrip('/')}"

        try:
            async with self._session.request(
                method=method, url=url, params=params, json=data
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            # Handle rate limiting
            if hasattr(e, "status") and e.status == 429:
                retry_after = int(response.headers.get("X-Requests-Available", "1"))
                if retry_after > 0:
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, method, params, data)
            raise

    # Competition endpoints
    async def get_competitions(
        self, areas: Optional[List[int]] = None, plan: Optional[str] = None
    ) -> List[Competition]:
        """Get all available competitions.

        Args:
            areas: Filter competitions by area IDs
            plan: Filter by plan (TIER_ONE, TIER_TWO, TIER_THREE, TIER_FOUR)

        Returns:
            List of Competition objects
        """
        params = {}
        if areas:
            params["areas"] = ",".join(map(str, areas))
        if plan:
            params["plan"] = plan

        data = await self._make_request("/competitions", params=params)
        return [Competition(**comp) for comp in data.get("competitions", [])]

    async def get_competition(
        self,
        competition_id: Optional[int] = None,
        competition_code: Optional[str] = None,
    ) -> Competition:
        """Get a specific competition by ID.

        Args:
            competition_id: The ID of the competition
            competition_code: The code of the competition

        Returns:
            Competition object
        """
        if not (bool(competition_id) or bool(competition_code)):
            raise ValueError(
                "Either competition id or competiton code should be provided"
            )
        data = await self._make_request(
            f"/competitions/{competition_id or competition_code}"
        )
        return Competition(**data)

    # Team endpoints
    async def get_teams(
        self,
        competition_id: int,
        season: Optional[int] = None,
        stage: Optional[str] = None,
    ) -> List[Team]:
        """Get teams for a specific competition.

        Args:
            competition_id: The ID of the competition
            season: Filter by season year
            stage: Filter by stage

        Returns:
            List of Team objects
        """
        params = {}
        if season:
            params["season"] = season
        if stage:
            params["stage"] = stage

        data = await self._make_request(
            f"/competitions/{competition_id}/teams", params=params
        )
        return [Team(**team) for team in data.get("teams", [])]

    async def get_team(self, team_id: int) -> Team:
        """Get a specific team by ID.

        Args:
            team_id: The ID of the team

        Returns:
            Team object
        """
        data = await self._make_request(f"/teams/{team_id}")
        return Team(**data)

    # Match endpoints
    async def get_matches(
        self,
        competition_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
        matchday: Optional[int] = None,
        group: Optional[str] = None,
        season: Optional[int] = None,
        stage: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Match]:
        """Get matches with optional filters.

        Args:
            competition_id: Filter by competition ID
            date_from: Start date for filtering matches
            date_to: End date for filtering matches
            status: Filter by match status
            matchday: Filter by matchday
            group: Filter by group
            season: Filter by season year
            stage: Filter by stage
            limit: Maximum number of matches to return (default: 10)
            offset: Offset for pagination (default: 0)

        Returns:
            List of Match objects
        """
        params = {"limit": limit, "offset": offset}

        if date_from:
            params["dateFrom"] = date_from.isoformat()
        if date_to:
            params["dateTo"] = date_to.isoformat()
        if status:
            params["status"] = status
        if matchday is not None:
            params["matchday"] = matchday
        if group:
            params["group"] = group
        if season:
            params["season"] = season
        if stage:
            params["stage"] = stage

        endpoint = (
            f"/competitions/{competition_id}/matches" if competition_id else "/matches"
        )
        data = await self._make_request(endpoint, params=params)
        return [Match(**match) for match in data.get("matches", [])]

    # async def get_match(self, match_id: int) -> Match:
    #     """Get a specific match by ID.

    #     Args:
    #         match_id: The ID of the match

    #     Returns:
    #         Match object
    #     """
    #     data = await self._make_request(f"/matches/{match_id}")
    #     return Match(**data)

    # # Area endpoints
    # async def get_areas(self) -> List[Dict[str, Any]]:
    #     """Get all available areas.

    #     Returns:
    #         List of area dictionaries
    #     """
    #     data = await self._make_request("/areas")
    #     return data.get("areas", [])

    # async def get_area(self, area_id: int) -> Dict[str, Any]:
    #     """Get a specific area by ID.

    #     Args:
    #         area_id: The ID of the area

    #     Returns:
    #         Area dictionary
    #     """
    #     return await self._make_request(f"/areas/{area_id}")

    # # Player endpoints
    # async def get_player(self, player_id: int) -> Dict[str, Any]:
    #     """Get a specific player by ID.

    #     Args:
    #         player_id: The ID of the player

    #     Returns:
    #         Player information
    #     """
    #     return await self._make_request(f"/persons/{player_id}")

    # # Standing endpoints
    # async def get_standings(
    #     self,
    #     competition_id: int,
    #     season: Optional[int] = None,
    #     matchday: Optional[int] = None,
    #     date: Optional[date] = None,
    # ) -> Dict[str, Any]:
    #     """Get standings for a competition.

    #     Args:
    #         competition_id: The ID of the competition
    #         season: Filter by season year
    #         matchday: Filter by matchday
    #         date: Filter by date

    #     Returns:
    #         Standings information
    #     """
    #     params = {}
    #     if season:
    #         params["season"] = season
    #     if matchday is not None:
    #         params["matchday"] = matchday
    #     if date:
    #         params["date"] = date.isoformat()

    #     return await self._make_request(
    #         f"/competitions/{competition_id}/standings", params=params
    #     )


# Example usage
async def example_usage():
    """Example usage of the FootballDataClient."""
    server_config = ServerConfig()
    async with FootballDataClient(server_config) as client:
        # Get all competitions
        # competitions = await client.get_competitions()
        # print(f"Found {len(competitions)} competitions")

        # # Get a specific competition
        pl = await client.get_competition(2021)  # Premier League
        print(f"\nPremier League: {pl.name}")

        # Get teams in a competition
        teams = await client.get_teams(2021, season=2023)  # PL teams for 2023
        print("\nTeams in Premier League 2023:")
        for team in teams[:5]:  # Show first 5 teams
            print(f"- {team.name} ({team.short_name})")

        # Get upcoming matches
        today = date.today()
        next_week = date(today.year, today.month, today.day + 7)
        matches = await client.get_matches(
            competition_id=2021, date_from=today, date_to=next_week, status="SCHEDULED"
        )
        print("\nUpcoming Premier League matches:")
        for match in matches[:5]:  # Show first 5 matches
            print(
                f"- {match.home_team['name']} vs {match.away_team['name']} on {match.utc_date}"
            )


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
