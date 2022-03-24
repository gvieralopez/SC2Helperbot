from abc import ABC, abstractmethod

import requests

from sc2bot.client.config import REALM_ID, BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET
from sc2bot.database.data import Race, League
from sc2bot.database.schema import PlayerStat, Player


class Resolver(ABC):
    @abstractmethod
    def resolve_player_stats(self, player: Player) -> list[PlayerStat]:
        ...

    @abstractmethod
    def resolve_player_display_name(self, player: Player) -> str:
        ...


class BlizzardResolver(Resolver):
    def __init__(self, base_url: str):
        self.base_url = base_url

    def resolve_player_stats(self, player: Player) -> list[PlayerStat]:
        ladder_summary = self.get_ladder_summary(player.profile_id, player.region_id)
        one_vs_one_ladders = filter(
            lambda ls: ls["localizedGameMode"].startswith("1v1"),
            ladder_summary["allLadderMemberships"],
        )
        ladder_infos = [
            self.get_ladder_info(player, ladder["ladderId"]) for ladder in one_vs_one_ladders
        ]
        return [build_player_stat(player, ladder_info) for ladder_info in ladder_infos]

    def resolve_player_display_name(self, player) -> str:
        return self.get_player_metadata(player)["name"]

    def get_ladder_summary(self, profile_id: int, region_id: int) -> dict:
        url = f"{self.base_url}/sc2/profile/{region_id}/{REALM_ID}/{profile_id}/ladder/summary"
        return self.make_get_request(url)

    def get_ladder_info(self, player: Player, ladder_id: str) -> dict:
        return self.make_get_request(
            f"{self.base_url}/sc2/profile/{player.region_id}/{REALM_ID}/{player.profile_id}/ladder/{ladder_id}"
        )

    def get_player_metadata(self, player) -> dict:
        return self.make_get_request(
            f"{self.base_url}/sc2/metadata/profile/{player.region_id}/{REALM_ID}/{player.profile_id}"
        )

    def make_get_request(self, url: str) -> dict:
        response = requests.get(url, params=self.get_params())
        if response.status_code == 200:
            return response.json()
        raise ValueError(f"API Response status not ok: {response}({response.content})")

    def get_params(self) -> dict:
        return {}


class BlizzardAuthorizedResolver(BlizzardResolver):
    def __init__(self, base_url: str, auth_url: str, client_id: str, client_secret: str):
        super().__init__(base_url)
        self.auth_url = auth_url
        self.client_id = client_id
        self.client_secret = client_secret

    def get_params(self) -> dict:
        return {"locale": "en_US", "access_token": self.get_access_token()}

    def get_access_token(self) -> str:
        response = requests.post(
            f"{self.auth_url}/oauth/token",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        raise ValueError(f"Token response status not ok: {response}({response.content})")


def build_player_stat(player: Player, ladder_info: dict) -> PlayerStat:
    league = League.from_raw(ladder_info["league"])
    mmr = ladder_info["ranksAndPools"][0]["mmr"]

    for team in ladder_info["ladderTeams"]:
        for member in team["teamMembers"]:
            if int(member["id"]) == player.profile_id:
                return PlayerStat(
                    player_id=player.id,
                    race=Race.from_raw(member["favoriteRace"]),
                    league=league,
                    mmr=mmr,
                    wins=team["wins"],
                    losses=team["losses"],
                    clan_tag=member.get("clanTag", ""),
                )


resolvers: list[Resolver] = [
    BlizzardAuthorizedResolver(
        "https://us.api.blizzard.com",
        "https://us.battle.net",
        BLIZZARD_CLIENT_ID,
        BLIZZARD_CLIENT_SECRET,
    ),
    BlizzardAuthorizedResolver(
        "https://eu.api.blizzard.com",
        "https://us.battle.net",
        BLIZZARD_CLIENT_ID,
        BLIZZARD_CLIENT_SECRET,
    ),
    BlizzardResolver("https://starcraft2.com/en-us/api"),
]
