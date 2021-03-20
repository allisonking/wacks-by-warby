"""Super simple text file db"""

import json
import time
from pathlib import Path

DATA_DIR = Path("data")


class Wackabase:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.json_path = data_dir / "data.json"
        self.last_success_path = data_dir / "last_success.txt"
        self.num_sales_path = data_dir / "num_sales.txt"

    def get_last_entry(self):
        """Returns an empty dictionary if the data file does not exist"""
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        return data

    def write_entry(self, entry: dict):
        print("writing to", self.json_path.absolute())
        with open(self.json_path, "w") as f:
            json.dump(entry, f)

    def get_last_num_sales(self):
        try:
            with open(self.num_sales_path) as f:
                num = f.read()
                return int(num)
        except FileNotFoundError:
            return 0

    def write_num_sales(self, num_sales):
        with open(self.num_sales_path, "w") as f:
            f.write(str(num_sales))

    def get_last_success(self):
        try:
            with open(self.last_success_path) as f:
                t = f.read()
                return float(t)
        except FileNotFoundError:
            return 0

    def write_success(self):
        now = time.time()
        with open(self.last_success_path, "w") as f:
            f.write(str(now))
