import logging
import os
from typing import Optional

from wacksbywarby.models import Sale

logger = logging.getLogger("shift4shop")


class Shift4Shop:
    def __init__(self, debug=False) -> None:
        self.key = os.getenv("SHIFT4SHOP_PRIVATE_KEY")
        self.shop_token = os.getenv("SHIFT4SHOP_SHOP_TOKEN")
        self.debug = debug

    def determine_sales(self, timestamp: Optional[str]) -> list[Sale]:
        """
        Query the Shift4Shop API for all orders since the given timestamp. Then transform these orders
        into a list of Sale objects
        """
        # TODO
        return []

    def get_num_sales(self) -> int:
        """
        Get the current total number of sales by querying the Shift4Shop API
        """
        # TODO
        return 0
