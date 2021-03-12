"""Super simple text file db"""

import json
import time

JSON_PATH = "data/data.json"
LAST_SUCCESS_PATH = "data/last_success.txt"


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

    @staticmethod
    def get_last_success():
        try:
            with open(LAST_SUCCESS_PATH) as f:
                t = f.read()
                return float(t)
        except FileNotFoundError:
            return 0

    @staticmethod
    def write_success():
        now = time.time()
        with open(LAST_SUCCESS_PATH, "w") as f:
            f.write(str(now))
