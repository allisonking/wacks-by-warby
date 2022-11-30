import logging
import os
from datetime import datetime
from typing import Optional

import requests

from wacksbywarby.constants import SHIFT4SHOP_ORDER_DATE_FORMAT, SHIFT4SHOP_TIME_FORMAT
from wacksbywarby.models import Sale

logger = logging.getLogger("shift4shop")

BASE_API = "https://apirest.3dcart.com/3dCartWebAPI/v1"
"""
Use all order statuses except for 7, not completed
From @rchhay:
1 = New
2 = Processing
3 = Partial
4 = Shipped
5 = Cancel
6 = Hold
7 = Not Completed
8 = Custom 1 (I think this is for gift card)
9 = Custom 2 (not being used i think)
10 = Custom 3 (also not used)
"""
ORDER_STATUSES = [1, 2, 3, 4, 5, 6, 8, 9, 10]


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

    def request_all_products(self):
        """
        A util function that is useful for figuring out the catalog IDs of werbies in
        shift4shop
        """
        response = requests.get(
            f"{BASE_API}/Products/", headers=self.headers, params={"limit": 100}
        )
        products = response.json()
        for product in products:
            print(product["SKUInfo"]["CatalogID"], product["SKUInfo"]["Name"], "\n")

    def determine_sales(self, timestamp: Optional[str]) -> list[Sale]:
        """
        Query the Shift4Shop API for all orders since the given timestamp. Then transform these orders
        into a list of Sale objects
        """
        params: dict = {"orderstatus": ORDER_STATUSES}
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
        sales: list[Sale] = []
        for order in orders:
            order_date_str = order["OrderDate"]
            order_date = datetime.strptime(order_date_str, SHIFT4SHOP_ORDER_DATE_FORMAT)
            if timestamp and order_date == datetime.strptime(
                timestamp, SHIFT4SHOP_TIME_FORMAT
            ):
                continue
            for item in order["OrderItemList"]:
                sales.append(
                    Sale(
                        listing_id=item["CatalogID"],
                        quantity=item["ItemUnitStock"],
                        num_sold=item["ItemQuantity"],
                        datetime=order_date,
                    )
                )
        # order sales by date
        ordered_sales = sorted(sales, key=lambda sale: sale.datetime)
        return ordered_sales

    def get_num_sales(self) -> int:
        """
        Get the current total number of sales by querying the Shift4Shop API
        """
        params = {
            "orderstatus": ORDER_STATUSES,
            # count the number of rows only
            "countonly": 1,
        }
        response = self._request_orders(params)
        return response.json()["TotalCount"]
