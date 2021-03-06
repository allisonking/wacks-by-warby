import logging
import os

import requests

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
        return raw_response.json()["results"][0]["Listings"]

    def get_inventory_state(self):
        items = self._request_inventory()
        # transform inventory to be keyed by listing id
        inventory_state = {
            str(item["listing_id"]): {
                "listing_id": str(item["listing_id"]),
                "title": item["title"],
                "quantity": item["quantity"],
                "state": item["state"],
            }
            for item in items
            if item["state"] == "active" or item["state"] == "sold_out"
        }
        logger.info("got inventory state, %s items", len(inventory_state))
        return inventory_state

    def get_inventory_state_diff(self, previous_inventory, current_inventory):
        if not previous_inventory:
            return {}

        state_diff = {}
        for listing_id in current_inventory:
            try:
                old_quantity = previous_inventory[listing_id]["quantity"]
            except KeyError:
                # a new item has been added since we haven't seen it in previous inventories
                logger.info(f"listing id {listing_id} is new!")
                old_quantity = 0

            new_quantity = current_inventory[listing_id]["quantity"]
            if new_quantity != old_quantity:
                state_diff[listing_id] = {
                    "listing_id": listing_id,
                    "title": current_inventory[listing_id]["title"],
                    "prev_quantity": old_quantity,
                    "current_quantity": new_quantity,
                }
        logger.info("got inventory state diff, %s diffs", len(state_diff))
        logger.info(f"diffs: {state_diff}")
        return state_diff
