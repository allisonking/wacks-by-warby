"""Super simple text file db"""
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from wacksbywarby.constants import SHIFT4SHOP_TIME_FORMAT, WACK_ERROR_SENTINEL
from wacksbywarby.models import SquareCredentials, EtsyCredentials

logger = logging.getLogger("db")

DATA_DIR = "data"


class Wackabase:
    def __init__(self, data_dir: str = DATA_DIR) -> None:
        data_path = Path(data_dir)
        self.last_success_path = data_path / "last_success.txt"
        self.num_sales_path = data_path / "num_sales.txt"
        self.timestamp_path = data_path / "timestamp.txt"
        self.square_creds = data_path / "square_creds.json"
        self.etsy_creds = data_path / "etsy_creds.json"

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
                t = f.read().strip()
                return t
        except FileNotFoundError:
            return None

    def write_square_creds(self, creds: SquareCredentials):
        with open(self.square_creds, "w") as f:
            f.write(creds.to_string())

    def get_square_creds(self):
        with open(self.square_creds, "r") as f:
            creds = f.read()
            return SquareCredentials.from_string(creds)

    def write_etsy_creds(self, creds: EtsyCredentials):
        with open(self.etsy_creds, "w") as f:
            f.write(creds.to_string())

    def get_etsy_creds(self):
        with open(self.etsy_creds, "r") as f:
            creds = f.read()
            return EtsyCredentials.from_string(creds)

