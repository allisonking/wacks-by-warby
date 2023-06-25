import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from wacks4square.constants import DATETIME_FMT as SQUARE_DATETIME_FMT


# deprecated
@dataclass
class Inventory:
    listing_id: str
    title: str
    quantity: int
    state: str

@dataclass
class Sale:
    listing_id: str
    quantity: int
    num_sold: int
    datetime: Optional[datetime]
    location: Optional[str]
    fallback_name: Optional[str]


@dataclass
class Shift4ShopSale(Sale):
    datetime: datetime


@dataclass
class Werby:
    name: str
    images: List[str]
    color: Optional[str]


@dataclass
class DiscordImage:
    url: str


@dataclass
class DiscordFooter:
    text: str


@dataclass
class DiscordEmbed:
    title: str
    color: Optional[int]
    image: Optional[DiscordImage]
    footer: Optional[DiscordFooter]


@dataclass
class SquareCredentials:
    access_token: str
    refresh_token: str
    short_lived: bool
    expires_at: datetime
    merchant_id: str
    token_type: str

    @classmethod
    def from_string(cls, string: str):
        data: dict = json.loads(string)
        data["expires_at"] = datetime.strptime(data["expires_at"], SQUARE_DATETIME_FMT)
        return cls(**data)

    def to_string(self):
        def prepare(x: SquareCredentials):
            as_dict = x.__dict__
            # convert the pesky timestamp
            as_dict["expires_at"] = datetime.strftime(x.expires_at, SQUARE_DATETIME_FMT)
            return as_dict

        return json.dumps(self, default=prepare)


@dataclass
class EtsyCredentials:
    access_token: str
    refresh_token: str
    expires_in: int
    # unixtime for when the access_token will expire
    expires_at: int
    token_type: str

    @classmethod
    def from_string(cls, string: str):
        data: dict = json.loads(string)
        return cls(**data)

    def to_string(self):
        def prepare(x: EtsyCredentials):
            as_dict = x.__dict__
            return as_dict

        return json.dumps(self, default=prepare)
