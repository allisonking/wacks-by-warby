import logging
import os
from typing import Dict

import requests

from wacksbywarby.models import Inventory

logger = logging.getLogger("etsy")


class Etsy:
    def __init__(self, debug=False) -> None:
        self.key = os.getenv("ETSY_API_KEY")
        self.shop_name = "wicksbywerby"
        self.debug = debug

    def _request_inventory(self):
        listings_endpoint_url = f"https://openapi.etsy.com/v2/shops/{self.shop_name}"
        raw_response = requests.get(
            listings_endpoint_url, params={"includes": "Listings", "api_key": self.key}
        )
        listings = raw_response.json()["results"][0]["Listings"]
        return listings

    def get_inventory_state(self) -> Dict[str, Inventory]:
        items = self._request_inventory()
        # transform inventory to be keyed by listing id
        inventory_state = {
            str(item["listing_id"]): Inventory(
                listing_id=str(item["listing_id"]),
                title=item["title"],
                quantity=item["quantity"],
                state=item["state"],
            )
            for item in items
            if item["state"] == "active" or item["state"] == "sold_out"
        }
        logger.info("got inventory state, %s items", len(inventory_state))
        return inventory_state
