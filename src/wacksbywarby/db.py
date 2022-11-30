"""Super simple text file db"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from wacksbywarby.constants import SHIFT4SHOP_TIME_FORMAT, WACK_ERROR_SENTINEL
from wacksbywarby.models import Inventory

logger = logging.getLogger("db")

DATA_DIR = "data"


class Wackabase:
    def __init__(self, data_dir: str = DATA_DIR) -> None:
        data_path = Path(data_dir)
        self.json_path = data_path / "data.json"
        self.last_success_path = data_path / "last_success.txt"
        self.num_sales_path = data_path / "num_sales.txt"
        self.timestamp_path = data_path / "timestamp.txt"

    def get_last_entry(self) -> dict[str, Inventory]:
        """Returns an empty dictionary if the data file does not exist"""
        try:
            with open(self.json_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        # transform to an Inventory object
        for key, value in data.items():
            data[key] = Inventory(**value)

        return data

    def write_entry(self, entry: dict[str, Inventory], pretty=False):
        indent = 4 if pretty else None
        with open(self.json_path, "w") as f:
            json.dump(entry, f, indent=indent, default=vars)

    def get_last_num_sales(self):
        try:
            with open(self.num_sales_path) as f:
                num = f.read()
                return int(num)
        except FileNotFoundError:
            logger.error("%s No file for last num sales", WACK_ERROR_SENTINEL)
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

    def write_timestamp(self, timestamp: datetime):
        with open(self.timestamp_path, "w") as f:
            f.write(timestamp.strftime(SHIFT4SHOP_TIME_FORMAT))

    def get_timestamp(self) -> Optional[str]:
        try:
            with open(self.timestamp_path) as f:
                t = f.read()
                return t
        except FileNotFoundError:
            return None
