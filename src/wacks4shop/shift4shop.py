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

    def _request_orders(self, params):
        return requests.get(f"{BASE_API}/Orders", params=params, headers=self.headers)

    def _request_product_details(self, catalog_id):
        return requests.get(f"{BASE_API}/Products/{catalog_id}", headers=self.headers)

    def determine_sales(self, timestamp: Optional[str]) -> list[Sale]:
        """
        Query the Shift4Shop API for all orders since the given timestamp. Then transform these orders
        into a list of Sale objects
        """
        params = {"orderstatus": 1}
        if timestamp:
            params["datestart"] = timestamp
        response = self._request_orders(params)

        if not response.ok:
            # when there are no new orders, this will 404. this will happen a lot, so we
            # really only need to log when it isn't a 404
            if response.status_code != 404:
                logger.error(
                    "Something has gone wrong! %s: %s",
                    response.status_code,
                    response.content,
                )
            return []

        orders = response.json()
        sales = []
        for order in orders:
            for item in order["OrderItemList"]:
                sales.append(
                    Sale(
                        listing_id=item["CatalogID"],
                        quantity=item["ItemUnitStock"],
                        num_sold=item["ItemQuantity"],
                    )
                )
        return sales

    def get_num_sales(self) -> int:
        """
        Get the current total number of sales by querying the Shift4Shop API
        """
        # TODO
        return 0
