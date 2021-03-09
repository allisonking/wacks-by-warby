import logging
import os

from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv


from wacksbywarby.db import Wackabase

logger = logging.getLogger("etsy")


class Etsy:
    def __init__(self, debug=False) -> None:
        self.key = os.getenv("ETSY_API_KEY")
        self.secret = os.getenv("ETSY_SECRET")
        self.request_token_url = "https://openapi.etsy.com/v2/oauth/request_token"
        self.url = "https://openapi.etsy.com/v2/listings/active"
        self.shop_name = "wicksbywerby"
        self.token = os.getenv("ETSY_TOKEN")
        self.token_secret = os.getenv("ETSY_TOKEN_SECRET")
        self.debug = debug

    def oauth(self):
        oauth = OAuth1Session(self.key, self.secret)
        fetch_response = oauth.fetch_request_token(
            self.request_token_url, data={"scope": "transactions_r"}
        )
        print(fetch_response)

    def create_etsy_session(self):
        session = OAuth1Session(self.key, self.secret, self.token, self.token_secret)
        return session

    def get_inventory_state(self):
        listings_endpoint_url = "https://openapi.etsy.com/v2/shops/wicksbywerby"
        session = self.create_etsy_session()
        raw_response = session.get(
            listings_endpoint_url, params={"includes": "Listings"}
        )
        items = raw_response.json()["results"][0]["Listings"]
        inventory_state = {
            str(item["listing_id"]): {
                "listing_id": str(item["listing_id"]),
                "title": item["title"],
                "quantity": item["quantity"],
            }
            for item in items
            if item["state"] == "active"
        }
        if self.debug:
            logger.info('got inventory state')
        return inventory_state

    def write_inventory(self):
        inventory = self.get_inventory_state()
        Wackabase.save_entry(inventory)
        if self.debug:
            logger.info('wrote inventory state')

    def get_inventory_state_diff(self):
        prev_state = Wackabase.get_last_entry()
        if not prev_state:
            return {}
        current_state = self.get_inventory_state()
        state_diff = {}
        for listing_id in prev_state:
            old_quantity = prev_state[listing_id]["quantity"]
            current_listing = current_state.get(listing_id) or {}
            new_quantity = current_listing.get("quantity")
            if not new_quantity:
                continue
            if new_quantity != old_quantity:
                state_diff[listing_id] = {
                    "listing_id": listing_id,
                    "title": current_listing["title"],
                    "prev_quantity": old_quantity,
                    "current_quantity": new_quantity,
                }
        if self.debug:
            logger.info('got inventory state diff')
        return state_diff


if __name__ == "__main__":
    load_dotenv()
    etsy = Etsy()
    # etsy.get_inventory_state()
    diff = etsy.get_inventory_state_diff()
    print(diff)
