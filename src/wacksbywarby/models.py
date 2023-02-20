from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Inventory:
    listing_id: str
    title: str
    quantity: int
    state: str


@dataclass
class InventoryDiff:
    listing_id: str
    title: str
    prev_quantity: int
    current_quantity: int


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
