import os

from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv


from wacksbywarby.db import Wackabase


class Etsy:
    def __init__(self) -> None:
        self.key = os.getenv("ETSY_API_KEY")
        self.secret = os.getenv("ETSY_SECRET")
        self.request_token_url = "https://openapi.etsy.com/v2/oauth/request_token"
        self.url = "https://openapi.etsy.com/v2/listings/active"
        self.shop_name = "wicksbywerby"
        self.token = os.getenv("ETSY_TOKEN")
        self.token_secret = os.getenv("ETSY_TOKEN_SECRET")

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
            item["listing_id"]: {
                "listing_id": item["listing_id"],
                "title": item["title"],
                "quantity": item["quantity"],
            }
            for item in items
            if item["state"] == "active"
        }
        return inventory_state

    def get_inventory_state_diff(self):
        prev_state = Wackabase.get_last_entry()
        if not prev_state:
            prev_state = self.get_inventory_state()
            Wackabase.save_entry(prev_state)
            return {}
        current_state = self.get_inventory_state()
        state_diff = {}
        for listing_id in prev_state:
            old_quantity = prev_state[listing_id]
            new_quantity = current_state.get(listing_id)
            if not new_quantity:
                continue
            diff = new_quantity - old_quantity
            state_diff["listing_id"] = {
                "listing_id": listing_id,
                "change_in_quantity": diff,
                "current_quantity": new_quantity,
            }
        return state_diff


if __name__ == "__main__":
    load_dotenv()
    etsy = Etsy()
    etsy.get_inventory_state()
