import json

DB_PATH = "werbies.json"


class Werbies:
    @staticmethod
    def get_embed_data(listing_id):
        try:
            with open(DB_PATH, "r") as f:
                id_to_data = json.load(f)
        except FileNotFoundError:
            id_to_data = {}
        data = id_to_data.get(listing_id)
        return data
