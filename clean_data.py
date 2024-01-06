import json
from dataclasses import dataclass
from enum import Enum

POINTS_DISTRIBUTION = [6, 5, 4, 3, 3, 2, 2, 1, 1, 1]


class Multipliers(Enum):
    TOP_25 = 2
    TOP_50 = 1.5
    TOP_100 = 1.25
    BASE = 1
    NON_IT = 0.75


@dataclass
class Vote:
    ranking: int
    choice_id: int
    choice_username: str
    base_weight: float = 0
    weight: float = 0

    @classmethod
    def from_json(cls, json_obj: dict):
        return cls(
            ranking=json_obj["ranking"],
            choice_id=json_obj["choiceId"],
            choice_username=json_obj["choiceUsername"],
        )

    def to_dict(self):
        return {
            "ranking": self.ranking,
            "choiceId": self.choice_id,
            "choiceUsername": self.choice_username,
            "weight": self.weight,
            "baseWeight": self.base_weight,
        }


@dataclass
class TierList:
    user_id: int
    username: str
    country: str
    country_rank: int
    rank: int
    votes: list[Vote]
    multiplier: Multipliers = Multipliers.BASE

    @classmethod
    def from_json(cls, json_obj: dict):
        return cls(
            user_id=json_obj["userId"],
            username=json_obj["username"],
            country=json_obj["country"],
            country_rank=json_obj["countryRank"],
            rank=json_obj["rank"],
            votes=[Vote.from_json(vote) for vote in json_obj["votes"]],
        )

    def to_dict(self):
        return {
            "userId": self.user_id,
            "username": self.username,
            "country": self.country,
            "countryRank": self.country_rank,
            "rank": self.rank,
            "multiplier": self.multiplier.value,
            "votes": [vote.to_dict() for vote in self.votes],
        }

    def to_anonymized_dict(self):
        return {
            "country": self.country,
            "multiplier": self.multiplier.value,
            "votes": [vote.to_dict() for vote in self.votes],
        }

    def is_valid(self):
        return len(self.votes) == 10

    def bootstrap_weights(self):
        self.bootstrap_multiplier()
        print(
            f"Voter multiplier: {self.multiplier} for player {self.username} ({self.country} #{self.country_rank})"
        )
        if not self.is_valid():
            return
        for vote, base_points in zip(self.votes, POINTS_DISTRIBUTION):
            vote.base_weight = base_points
            vote.weight = base_points * self.multiplier.value

    def bootstrap_multiplier(self):
        # Arge should have 2x
        if self.user_id == 11215030:
            self.multiplier = Multipliers.TOP_25
            return
        if not self.country == "IT":
            self.multiplier = Multipliers.NON_IT
            return
        if self.country_rank is None:
            self.multiplier = Multipliers.BASE
            return
        if self.country_rank <= 25:
            self.multiplier = Multipliers.TOP_25
            return
        if self.country_rank <= 50:
            self.multiplier = Multipliers.TOP_50
            return
        if self.country_rank <= 100:
            self.multiplier = Multipliers.TOP_100
            return

        self.multiplier = Multipliers.BASE


@dataclass
class Data:
    tiers: list[TierList]

    @classmethod
    def from_json(cls, json_obj: dict):
        return cls(tiers=[TierList.from_json(tierlist) for tierlist in json_obj])

    def process_data(self):
        for tier in self.tiers:
            tier.bootstrap_weights()

    def to_dict(self):
        return [tier.to_dict() for tier in self.tiers]

    def to_anonymized_dict(self):
        return [tier.to_anonymized_dict() for tier in self.tiers if tier.is_valid()]


def main():
    with open("votes.json") as f:
        data = Data.from_json(json.load(f))
    data.process_data()
    with open("anonymized_and_cleaned_votes.json", "w") as f:
        json.dump(data.to_anonymized_dict(), f, indent=4)


if __name__ == "__main__":
    main()
