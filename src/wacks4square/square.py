import logging
import os
from datetime import datetime
from typing import Optional

import requests

from wacksbywarby.constants import SHIFT4SHOP_ORDER_DATE_FORMAT, SHIFT4SHOP_TIME_FORMAT
from wacksbywarby.models import Sale
from dotenv import load_dotenv

logger = logging.getLogger("shift4shop")

BASE_API = "https://apirest.3dcart.com/3dCartWebAPI/v2"

class Square:
    def __init__(self, debug=False) -> None:
        # TODO update these keys
        self.key = os.getenv("SHIFT4SHOP_PRIVATE_KEY")
        self.shop_token = os.getenv("SHIFT4SHOP_SHOP_TOKEN")
        self.debug = debug
        self.headers = {
            "SecureURL": "wicksbywerby.com",
            "PrivateKey": self.key,
            "Token": self.shop_token,
        }

    def _search_orders(self, params):
        return requests.get(f"{BASE_API}/Orders/Search", params=params, headers=self.headers)

    # def _request_product_details(self, catalog_id):
    #     return requests.get(f"{BASE_API}/Products/{catalog_id}", headers=self.headers)

    # TODO replace with this one https://developer.squareup.com/reference/square/catalog-api/list-catalog
    # def request_all_products(self):
    #     """
    #     A util function that is useful for figuring out the catalog IDs of werbies in
    #     shift4shop
    #     """
    #     response = requests.get(
    #         f"{BASE_API}/Products/", headers=self.headers, params={"limit": 100}
    #     )
    #     products = response.json()
    #     for product in products:
    #         print(product["SKUInfo"]["CatalogID"], product["SKUInfo"]["Name"], "\n")
    def _get_orders_since_timestamp(self, timestamp):
        # TODO convert last_timestamp to correct format
        # TODO generate now in correct format
        end_at = "123"
        new_orders_response = self._search_orders({
            "location_ids": [],
            "return_entries": False,
            "query": {"filter": {"date_time_filter": {"closed_at": {"start_at": timestamp, "end_at": end_at}},
                                 # TODO sort by the right order so we announce earlier sales earlier?
                      "state_filter": {"states": ["COMPLETED"]}}, "sort": {"sort_field": "CLOSED_AT",
                                                                           "sort_order": "ASC"}}
        })
        orders = new_orders_response.json()['orders']
        return orders

    def get_sales_since_timestamp(self, timestamp) -> list[Sale]:
        """
        Query the Shift4Shop API for all orders since the given timestamp. Then transform these orders
        into a list of Sale objects. Manually dedupe incomplete orders from all orders using
        order id as the API doesn't support filtering by multiple order statuses.
        """
        # TODO convert last_timestamp to correct format
        # TODO generate now in correct format
        now = "123"
        new_orders_response = self._get_orders_since_timestamp(timestamp)
        sales: list[Sale] = []
        for order in new_orders_response:
            order_created_at = order['created_at']
            for item in order["line_items"]:
                sales.append(
                    Sale(
                        # TODO might need to map these uids to the canonical listing_id from werbies.json
                        listing_id=item["uid"],
                        # may need to query catalog to get num items left
                        # quantity=item["ItemUnitStock"],
                        num_sold=item["quantity"],
                        datetime=order_created_at,
                    )
                )
        return sales

    def get_num_sales(self, last_timestamp: str, prev_num_sales: int) -> int:
        """
        Get total number of sales by using previously stored sales and timestamp and getting any new sales since
        then.
        """
        new_orders_response = self._get_orders_since_timestamp(last_timestamp)
        num_new_orders = 0
        for order in new_orders_response.json()['orders']:
            num_new_orders += len(order['line_items'])

        num_total_sales = prev_num_sales + num_new_orders
        return num_total_sales


if __name__ == "__main__":
    load_dotenv()
    shift = Shift4Shop(debug=True)
    response = shift.get_num_sales()
    print(response)
