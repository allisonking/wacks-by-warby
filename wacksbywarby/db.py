"""Super simple text file db"""

import json

DB_PATH = "data/data.json"


class Wackabase:
    @staticmethod
    def get_last_entry():
        """Returns an empty dictionary if the data file does not exist"""
        try:
            with open(DB_PATH, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        return data

    @staticmethod
    def save_entry(entry: dict):
        with open(DB_PATH, "w") as f:
            json.dump(entry, f)
