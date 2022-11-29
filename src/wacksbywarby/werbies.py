import json
from typing import Optional

from wacksbywarby.models import Werby

DB_PATH = "werbies.json"


class Werbies:
    @staticmethod
    def get_embed_data(listing_id) -> Optional[Werby]:
        try:
            with open(DB_PATH, "r") as f:
                id_to_data = json.load(f)
        except FileNotFoundError:
            id_to_data = {}
        data = id_to_data.get(listing_id)
        if "color" not in data:
            data["color"] = None

        return Werby(**data) if data else None
