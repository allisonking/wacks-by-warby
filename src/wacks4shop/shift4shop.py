import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple

import requests
from dotenv import load_dotenv

from wacksbywarby.constants import SHIFT4SHOP_ORDER_DATE_FORMAT, SHIFT4SHOP_TIME_FORMAT
from wacksbywarby.models import Shift4ShopSale

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
        """https://apirest.3dcart.com/v2/orders/index.html#retrieve-a-list-of-orders"""
        logger.info(f"requesting orders with params {params}")
        return requests.get(f"{BASE_API}/Orders", params=params, headers=self.headers)

    def _request_product_details(self, catalog_id):
        """https://apirest.3dcart.com/v2/products/index.html#retrieve-a-list-of-products"""
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
        return products

    def determine_sales(
        self, timestamp: Optional[str]
    ) -> Tuple[list[Shift4ShopSale], Optional[str]]:
        """
        Query the Shift4Shop API for all orders since the given timestamp. Then transform these orders
        into a list of Shift4ShopSale objects. Manually dedupe incomplete orders from all orders using
        order id as the API doesn't support filtering by multiple order statuses.

        Timestamp may be null if this is the first time running the app so we want to list
        every order
        """
        params: dict = {"limit": 100}
        if timestamp:
            params["datestart"] = timestamp
        all_orders_response = self._request_orders(params)

        if not all_orders_response.ok:
            # when there are no new orders, this will 404. this will happen a lot, so we
            # really only need to log when it isn't a 404
            if all_orders_response.status_code != 404:
                logger.error(
                    "Something has gone wrong with getting all orders! %s: %s",
                    all_orders_response.status_code,
                    all_orders_response.content,
                )

            return ([], timestamp)

        all_orders_since_timestamp = all_orders_response.json()

        # Grab the most recent timestamp from ALL sales as opposed to just completed sales
        # This lets us keep the waterline not too far from the last sale in the event that
        # there are a lot of incompleted sales. This is to solve a bug for when there are >300
        # sales between waterlines, which makes us miss orders.
        try:
            most_recent_order_timestamp = sorted(
                all_orders_since_timestamp,
                key=lambda x: x["OrderDate"],
                reverse=True,
            )[0]["OrderDate"]
        except IndexError:
            # if we can't find anything, use the timestamp we were given
            logger.error("Could not get most recent order date, using %s instead", timestamp)
            most_recent_order_timestamp = timestamp

        completed_orders = [
            order
            for order in all_orders_since_timestamp
            if order["OrderStatusID"] != INCOMPLETE_ORDER_STATUS
        ]

        sales: list[Shift4ShopSale] = []
        for order in completed_orders:
            order_date_str = order["OrderDate"]
            order_date = datetime.strptime(order_date_str, SHIFT4SHOP_ORDER_DATE_FORMAT)
            # if we were passed a timestamp of the last order, make sure we don't append that
            # last order again
            if timestamp and order_date == datetime.strptime(
                timestamp, SHIFT4SHOP_TIME_FORMAT
            ):
                continue
            for item in order["OrderItemList"]:
                sales.append(
                    Shift4ShopSale(
                        listing_id=item["CatalogID"],
                        quantity=item["ItemUnitStock"],
                        num_sold=item["ItemQuantity"],
                        datetime=order_date,
                        location=None,
                        fallback_name=item["ItemDescription"].split("<br>")[0],
                    )
                )
        # order sales by date
        ordered_sales = sorted(sales, key=lambda sale: sale.datetime)
        return (ordered_sales, most_recent_order_timestamp)

    def _internal_get_num_sales(self, additional_query_filters: dict) -> int:
        """
        Get the number of total sales using the shift4shop orders search API
        Filter out any that are incomplete orders

        See _request_orders() for filters that can be applied to the search query.
        Examples include "limit", "orderstatus", "datestart"
        """
        total_orders_response = self._request_orders(
            {"limit": 300, **additional_query_filters}
        )
        num_sales = 0
        for order in total_orders_response.json():
            if order["OrderStatusID"] != INCOMPLETE_ORDER_STATUS:
                num_sales += len(order["OrderItemList"])

        return num_sales

    def legacy_get_num_sales(self) -> int:
        """
        This is a stopgap solution that works by querying all the orders and
        counting up the items within each order, to an upper limit of around 300 orders.
        This has become quite slow already at around 100 orders, taking up to 1 minute
        to complete the request
        """
        logger.info("getting legacy num sales")
        num_sales = self._internal_get_num_sales({"limit": 300})
        return num_sales

    def get_num_sales(self, timestamp: str, prev_num_sales: int) -> int:
        """
        We store the previous number of sales so we can just get the new sales
        since the last timestamp
        """
        logger.info("getting num sales")
        num_new_sales = self._internal_get_num_sales({"datestart": timestamp})
        num_total_sales = prev_num_sales + num_new_sales
        return num_total_sales


if __name__ == "__main__":
    load_dotenv()
    shift = Shift4Shop(debug=True)
    prev_num_sales = 0
    timestamp = (datetime.now() - timedelta(days=1)).strftime("%m/%d/%Y %H:%M:%S")
    num_sales = shift.get_num_sales(timestamp, 0)
    print(num_sales)
