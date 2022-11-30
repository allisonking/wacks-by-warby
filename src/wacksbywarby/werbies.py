import json
from typing import Literal, Optional

from wacksbywarby.models import Werby

DB_PATH = "werbies.json"
IdType = Literal["etsy", "shift4shop"]


class Werbies:
    @staticmethod
    def get_embed_data(listing_id: str, id_type: IdType = "etsy") -> Optional[Werby]:
        id_to_data = Werbies.read_werbies_file()

        data = None
        if id_type == "etsy":
            data = id_to_data.get(listing_id)
        else:
            for werby in id_to_data.values():
                if werby.get("shift4shop_id") == listing_id:
                    data = werby
                    break

        if data is None:
            return None

        return Werby(name=data["name"], images=data["images"], color=data.get("color"))

    @staticmethod
    def read_werbies_file() -> dict:
        try:
            with open(DB_PATH, "r") as f:
                id_to_data = json.load(f)
        except FileNotFoundError:
            id_to_data = {}
        return id_to_data
