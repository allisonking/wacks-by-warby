import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json

import requests
from dotenv import load_dotenv

from wacksbywarby.constants import SQUARE_TIME_FORMAT
from wacksbywarby.models import Sale
from wacksbywarby.wack import announce_new_sales
from wacksbywarby.werbies import Werbies

logger = logging.getLogger("square")

# prod
BASE_API = "https://connect.squareup.com/v2"

load_dotenv()
MAIN_LOCATION_ID = os.getenv("SQUARE_MAIN_LOCATION_ID")
BACKUP_LOCATION_ID = os.getenv("SQUARE_BACKUP_LOCATION_ID")
LOCATION_IDS = [MAIN_LOCATION_ID, BACKUP_LOCATION_ID]
LOCATION_ID_TO_NAME = {MAIN_LOCATION_ID: "Main", BACKUP_LOCATION_ID: "Backup"}


class Square:
    def __init__(self, debug=False) -> None:
        self.access_token = os.getenv("SQUARE_ACCESS_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        self.debug = debug

    def _search_orders(self, params):
        logger.info(f"search orders request with params {params}")
        response = requests.post(
            f"{BASE_API}/orders/search", json=params, headers=self.headers
        )
        if response.ok:
            data = response.json()
            return data.get("orders", [])
        logger.error(f"error in search orders request: {response}")
        raise Exception(response.json())

    def _get_order(self, order_id):
        logger.info(f"making get order request for order id {order_id}")
        response = requests.get(f"{BASE_API}/orders/{order_id}", headers=self.headers)
        if response.ok:
            data = response.json()
            return data
        logger.error(f"error getting order: {response}")
        raise Exception(response.json())

    def request_all_products(self):
        """
        A util function that is useful for figuring out the catalog IDs of werbies in
        square

        https://developer.squareup.com/reference/square/catalog-api/list-catalog
        """
        response = requests.get(
            f"{BASE_API}/catalog/list", headers=self.headers, params={"types": ["ITEM"]}
        )
        products = response.json().get("objects")
        all_variations = []
        for product in products:
            if product["is_deleted"]:
                print("DELETED", product["item_data"]["name"])
                continue
            variation_str = product["item_data"]["name"]
            for variation in product.get("item_data", {}).get("variations", []):
                variation_str += (
                    f'|{variation["item_variation_data"]["name"]}<{variation["id"]}>'
                )
            all_variations.append(variation_str)
        print("\n\n".join(all_variations))

    def _get_orders_between_timestamps(self, start_timestamp: str, end_timestamp: str) -> List[Dict[str, any]]:
        if end_timestamp is None:
            end_timestamp = datetime.utcnow().isoformat()
        params = {
            "limit": 500,
            "location_ids": LOCATION_IDS,
            # return full order data, not just order id
            "return_entries": False,
            "query": {
                "filter": {
                    "date_time_filter": {
                        "closed_at": {"start_at": start_timestamp, "end_at": end_timestamp}
                    },
                    "state_filter": {"states": ["COMPLETED"]},
                },
                # there seems to be some implicit hard limits on the square API,
                # no matter how big of a date_time_filter or limit you provide, sometimes orders are truncated.
                # so we need to sort by desc to ensure the most recent items aren't truncated
                "sort": {"sort_field": "CLOSED_AT", "sort_order": "DESC"},
            },
        }
        new_orders_response = self._search_orders(params)
        return new_orders_response

    def _get_orders_since_timestamp(self, start_timestamp: str) -> List[Dict[str, any]]:
        end_timestamp = datetime.utcnow().isoformat()
        orders = self._get_orders_between_timestamps(start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        return orders

    def get_sales_since_timestamp(self, start_timestamp: Optional[str], end_timestamp: Optional[str]) -> List[Sale]:
        """
        Query the square API for all orders since the given timestamp. Then transform these orders
        into a list of Sale objects.

        last_timestamp datetime string in isoformat, may be null if wacks is running for the first time
        """
        if not start_timestamp:
            start_timestamp = self._get_default_start_time_in_isoformat()
        if not end_timestamp:
            end_timestamp = datetime.utcnow().isoformat()
        logger.info(f"getting num sales, start timestamp {start_timestamp}")
        new_orders_response = self._get_orders_between_timestamps(start_timestamp, end_timestamp)
        sales = []
        for order in new_orders_response:
            line_items = order.get("line_items", [])
            if not line_items:
                print(order)
            for item in line_items:
                listing_id = item.get("catalog_object_id")
                if not listing_id:
                    print(f'missing listing id order: {json.dumps(order)}')
                    print(f'item {json.dumps(item)}')
                    continue
                if 'Fee' in item["name"]:
                    print(f'skipping credit card service fee, item: {item}')
                    continue
                created_at = order["created_at"]
                # some have milliseconds and some do not so let's strip the milliseconds out
                created_at = re.sub(r"\..+Z", "", created_at)
                # remove Z at the end for consistency
                created_at = created_at.replace("Z", "")
                try:
                    sale_time = datetime.strptime(created_at, SQUARE_TIME_FORMAT)
                except ValueError as e:
                    logger.exception(
                        f"error converting order timestamp for order: {order}, item: {item}"
                    )
                    continue
                try:
                    num_sold = int(item["quantity"])
                except ValueError as e:
                    logger.exception(
                        f"error converting quantity to int for order: {order}, item: {item}"
                    )
                    continue
                print(item["name"], item["variation_name"])

                sale = Sale(
                    # catalog_object_id is the variation id rather than the object id so be sure to store variation id
                    # in werbies.json rather than the catalog item id itself
                    name=item["name"],
                    order_id=order["id"],
                    variation_name=item["variation_name"],
                    listing_id=item["catalog_object_id"],
                    num_sold=num_sold,
                    # TODO hardcode this for now since it seems like we need to make a new request to get the actual value
                    quantity=10,
                    datetime=sale_time,
                    # location is a square unique feature in which sales can be made from specific locations
                    location=LOCATION_ID_TO_NAME[order["location_id"]],
                )
                sales.append(sale)
        return sales

    def get_num_sales(self, last_timestamp: Optional[str], prev_num_sales: int) -> int:
        """
        Get total number of sales by using previously stored sales and timestamp and getting any new sales since
        then. Note that there's some hard limit in Square's API so this doesn't actually return all the orders.
        Use the sort by field to ensure you get either the latest orders or the earliest orders but know there's
        no guarantee that the results weren't truncated.

        last_timestamp datetime string in isoformat
        """
        logger.info(
            f"getting num sales, last_timestamp {last_timestamp}, prev_num_sales: {prev_num_sales}"
        )
        # bump timestamp to avoid pulling double counting sales
        if last_timestamp:
            timestamp = (
                datetime.strptime(last_timestamp, SQUARE_TIME_FORMAT)
                + timedelta(seconds=1)
            ).isoformat()
        else:
            timestamp = self._get_default_start_time_in_isoformat()
        new_orders_response = self._get_orders_since_timestamp(timestamp)
        num_new_orders = 0
        for order in new_orders_response:
            line_items = order.get("line_items", [])
            num_new_orders += len(line_items)
        num_total_sales = prev_num_sales + num_new_orders
        return num_total_sales

    def get_num_sales_slow(self) -> int:
        """
        Get total number of sales by using poor perf method of querying all orders
        from square and counting up all line items
        """
        logger.info("get num sales slow")
        start_time = self._get_default_start_time_in_isoformat()
        new_orders_response = self._get_orders_since_timestamp(start_time)
        num_orders = 0
        for order in new_orders_response:
            line_items = order.get("line_items", [])
            if not line_items:
                logger.info(f"refunded order {order}")
            num_orders += len(line_items)
        logger.info(f"found {num_orders} items sold via slow method")
        return num_orders

    def get_order_breakdown_by_day(self):
        # start_time = datetime.fromisoformat(self._get_default_start_time_in_isoformat())
        first_end_time = datetime.utcnow() - timedelta(weeks=12)
        first_half_sales = self.get_sales_since_timestamp(self._get_default_start_time_in_isoformat(), first_end_time.isoformat())
        second_half_start_time = first_end_time + timedelta(seconds=1)
        second_half_sales = self.get_sales_since_timestamp(second_half_start_time.isoformat(), None)
        sales = [*first_half_sales, *second_half_sales]
        # now = datetime.utcnow()
        # # months = now.year - start_time.year * 12 + now.month - start_time.year
        # for month in range(0, months):

        from collections import defaultdict
        import json
        groups = defaultdict(list)
        num_sales = 0
        import csv
        with open('sales_by_day.csv', 'w', newline='') as file:
            writer = csv.writer(file)

            for sale in sales:
                num_sales += sale.num_sold
                eastern_time_stamp = sale.datetime - timedelta(hours=5)
                date = f"{eastern_time_stamp.month}-{eastern_time_stamp.day}-{eastern_time_stamp.year}"
                print_data = {'num_sold': sale.num_sold, 'timestamp': sale.datetime.isoformat(), 'name': sale.name, 'variation_name': sale.variation_name, 'order_id': sale.order_id }
                writer.writerow([sale.num_sold, sale.name, sale.variation_name, eastern_time_stamp.isoformat(), sale.order_id])
                groups[date].append(print_data)
        print(len(sales))
        print('num sales', num_sales)
        groups_list = []
        for key, value in groups.items():
            groups_list.append({'date': key, 'sales': value})
        data_sorted = sorted(groups_list, key=lambda x: datetime.strptime(x['date'], '%m-%d-%Y'))

        pretty_groups = json.dumps(data_sorted)
        print(pretty_groups)


    @staticmethod
    def _get_default_start_time_in_isoformat() -> str:
        """
        supply the farthest back in time we should look for square sales
        """
        start_time = datetime(2022, 6, 11).isoformat()
        return start_time


if __name__ == "__main__":
    load_dotenv()
    square = Square(debug=True)
    # start_time = (datetime.utcnow() - timedelta(hours=300)).isoformat()
    # sales = square.get_sales_since_timestamp(start_time)
    square.get_order_breakdown_by_day()
    # print(sales)
