from dataclasses import dataclass


@dataclass
class Inventory:
    listing_id: str
    title: str
    quantity: int
    state: str
