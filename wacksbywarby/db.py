"""Super simple text file db"""

import json

JSON_PATH = "data/data.json"


class Wackabase:
    @staticmethod
    def get_last_entry():
        """Returns an empty dictionary if the data file does not exist"""
        try:
            with open(JSON_PATH, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        return data

    @staticmethod
    def save_entry(entry: dict):
        with open(JSON_PATH, "w") as f:
            json.dump(entry, f)
