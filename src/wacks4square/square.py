import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Any

import requests

# from wacksbywarby.constants import SHIFT4SHOP_ORDER_DATE_FORMAT, SHIFT4SHOP_TIME_FORMAT
# from wacksbywarby.models import Sale
from dotenv import load_dotenv

logger = logging.getLogger("square")

# prod
BASE_API = "https://connect.squareup.com/v2"
# sandbox
# BASE_API = "https://connect.squareupsandbox.com/v2"

TEST_LOCATION_ID = "LF63C50H5VTEK"
BACKUP_TEST_LOCATION_ID = "LHTYTJXMD1TBW"


class Square:
    def __init__(self, debug=False) -> None:
        self.access_token = os.getenv("SQUARE_ACCESS_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        self.debug = debug

    def _search_orders(self, params):
        response = requests.post(f"{BASE_API}/orders/search", json=params, headers=self.headers)
        if response.ok:
            data = response.json()
            return data.get("orders", [])
        print(response)
        raise Exception(response.json())

    def _get_order(self, order_id):
        response = requests.get(f"{BASE_API}/orders/{order_id}", headers=self.headers)
        if response.ok:
            data = response.json()
            return data
        print(response)
        raise Exception(response.json())


    # def _request_product_details(self, catalog_id):
    #     return requests.get(f"{BASE_API}/Products/{catalog_id}", headers=self.headers)

    def request_all_products(self):
        """
        A util function that is useful for figuring out the catalog IDs of werbies in
        square

        https://developer.squareup.com/reference/square/catalog-api/list-catalog
        """
        response = requests.get(
            f"{BASE_API}/catalog/list", headers=self.headers, params={"types": ["ITEM"]}
        )
        # need some items in catalog to test this out
        # right now returns empty in sandbox
        print('all products response', response.json())
        products = response.json().get("objects")
        for product in products:
            print(product["id"], product["item_data"]["name"], "\n")

    def _get_orders_since_timestamp(self, timestamp):
        end_at = datetime.utcnow().isoformat()
        new_orders_response = self._search_orders({
            "location_ids": [TEST_LOCATION_ID],
            "return_entries": False,
            "query": {"filter": {"date_time_filter": {"closed_at": {"start_at": timestamp, "end_at": end_at}},
                      # "state_filter": {"states": ["COMPLETED"]}
                        },
                      # "sort": {"sort_field": "CLOSED_AT", "sort_order": "DESC"}
                      "sort": {"sort_field": "CREATED_AT", "sort_order": "DESC"}
                      }
        })
        return new_orders_response

    def get_sales_since_timestamp(self, timestamp):
        """
        QueRy the square API for all orders since the given timestamp. Then transform these orders
        into a list of Sale objects.
        """
        new_orders_response = self._get_orders_since_timestamp(timestamp)
        sales = []
        for order in new_orders_response:
            order_created_at = order['created_at']
            for item in order["line_items"]:
                # TODO placeholder code to avoid importing Sale type
                sale = {"listing_id": item["uid"],
                        "num_sold": item["quantity"],
                        "datetime": order_created_at
                        }
                print(sale)
                sales.append(sale)
                # sales.append(
                #     Sale(
                #         # TODO might need to map these uids to the canonical listing_id from werbies.json
                #         listing_id=item["uid"],
                #         # may need to query catalog to get num items left
                #         # quantity=item["ItemUnitStock"],
                #         num_sold=item["quantity"],
                #         datetime=order_created_at,
                #     )
                # )
        return sales

    def get_num_sales(self, last_timestamp: str, prev_num_sales: int) -> int:
        """
        Get total number of sales by using previously stored sales and timestamp and getting any new sales since
        then.
        """
        # TODO always save timestamps as utc
        new_orders_response = self._get_orders_since_timestamp(last_timestamp)
        print(new_orders_response)
        num_new_orders = 0
        for order in new_orders_response:
            print(order)
            num_new_orders += len(order['line_items'])

        num_total_sales = prev_num_sales + num_new_orders
        return num_total_sales


if __name__ == "__main__":
    load_dotenv()
    square = Square(debug=True)
    start_time = (datetime.utcnow() - timedelta(hours=300)).isoformat()
    num_sales_response = square.get_num_sales(start_time, 123)
    print(num_sales_response)
    # catalog_response = square.request_all_products()
    # print(catalog_response)
    # sales_since_response = square.get_sales_since_timestamp(start_time)
    # square.request_all_products()
