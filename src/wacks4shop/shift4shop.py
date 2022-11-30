import logging
import os
from typing import Optional

import requests

from wacksbywarby.models import Sale

logger = logging.getLogger("shift4shop")

BASE_API = "https://apirest.3dcart.com/3dCartWebAPI/v1"


class Shift4Shop:
    def __init__(self, debug=False) -> None:
        self.key = os.getenv("SHIFT4SHOP_PRIVATE_KEY")
        self.shop_token = os.getenv("SHIFT4SHOP_SHOP_TOKEN")
        self.debug = debug
        self.headers = {
            "SecureURL": "wicksbywerby.com",
            "PrivateKey": self.key,
            "Token": self.shop_token,
        }

    def _get_orders(self, params):
        return requests.get(f"{BASE_API}/Orders", params=params, headers=self.headers)

    def determine_sales(self, timestamp: Optional[str]) -> list[Sale]:
        """
        Query the Shift4Shop API for all orders since the given timestamp. Then transform these orders
        into a list of Sale objects
        """
        params = {"orderstatus": 1}
        if timestamp:
            params["datestart"] = timestamp
        orders = self._get_orders(params)
        return []

    def get_num_sales(self) -> int:
        """
        Get the current total number of sales by querying the Shift4Shop API
        """
        # TODO
        return 0
