import logging
import os
from datetime import datetime
from typing import Optional

import requests

from wacksbywarby.constants import SHIFT4SHOP_ORDER_DATE_FORMAT, SHIFT4SHOP_TIME_FORMAT
from wacksbywarby.models import Sale
from dotenv import load_dotenv

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
INCOMPLETE_ORDER_STATUS = 7


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
        into a list of Sale objects. Manually dedupe incomplete orders from all orders using
        order id as the API doesn't support filtering by multiple order statuses.
        """
        params: dict = {}
        if timestamp:
            params["datestart"] = timestamp
        all_orders_response = self._request_orders(params)

        incomplete_orders_params: dict = {"orderstatus": 7}
        if timestamp:
            incomplete_orders_params["datestart"] = timestamp
        incomplete_orders_response = self._request_orders(incomplete_orders_params)
        incomplete_order_ids = {order["OrderID"] for order in incomplete_orders_response.json()}
        completed_orders = [order for order in all_orders_response.json() if order["OrderID"] not in incomplete_order_ids]

        if not all_orders_response.ok or not incomplete_orders_response.ok:
            # when there are no new orders, this will 404. this will happen a lot, so we
            # really only need to log when it isn't a 404
            if all_orders_response.status_code != 404:
                logger.error(
                    "Something has gone wrong with getting all orders! %s: %s",
                    all_orders_response.status_code,
                    all_orders_response.content,
                )
            if incomplete_orders_response.status_code != 404:
                logger.error(
                    "Something has gone wrong with getting incomplete orders! %s: %s",
                    incomplete_orders_response.status_code,
                    incomplete_orders_response.content,
                )
            return []

        sales: list[Sale] = []
        for order in completed_orders:
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
        Get the current total number of sales by querying the Shift4Shop API.
        The API only supports filtering by 1 order status at a time so get the
        completed orders by taking the difference between all the orders without
        any filtering and the number of orders in the "not completed" status.
        Additionally, there's a default "limit" applied (10) if you don't send that param
        and an upper bound to how many orders can be returned at once so this is just
        a stopgap solution.

        Ultimately, we probably need to store previous num sales in the DB and use datestart
        or invoicenumberstart in the future.
        """
        not_completed_orders_response = self._request_orders({
            "orderstatus": INCOMPLETE_ORDER_STATUS,
            "limit": 300
        })
        num_not_completed_orders = 0
        for order in not_completed_orders_response.json():
            num_not_completed_orders += len(order["OrderItemList"])

        total_orders_response = self._request_orders({"limit": 300})
        num_total_orders = 0
        for order in total_orders_response.json():
            num_total_orders += len(order["OrderItemList"])

        num_sales = num_total_orders - num_not_completed_orders
        return num_sales


if __name__ == "__main__":
    load_dotenv()
    shift = Shift4Shop(debug=True)
    response = shift.get_num_sales()
    print(response)
