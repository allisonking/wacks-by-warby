import json
from typing import Literal, Optional

from wacksbywarby.models import Werby

DB_PATH = "werbies.json"
IdType = Literal["etsy", "shift4shop", "square"]


class Werbies:
    @staticmethod
    def get_embed_data(listing_id: str, id_type: IdType = "etsy") -> Optional[Werby]:
        id_to_data = Werbies.read_werbies_file()

        data = None
        if id_type == "etsy":
            data = id_to_data.get(listing_id)
        elif id_type == "square":
            for werby in id_to_data.values():
                # square data is stored as an array with each variation which has its own id e.g. "4oz tin", "Wax melt"
                variations = [variation for variation in werby.get("square_data", []) if variation["id"] == listing_id]
                if variations:
                    data = werby
                    variation_name = variations[0]["variation"]
                    if variation_name != "Regular":
                        # include the name of the variation to distinguish the different sales
                        data["name"] = f"{werby['name']} ({variation_name})"
                    break
        elif id_type == "shift4shop":
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
