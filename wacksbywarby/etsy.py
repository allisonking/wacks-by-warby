from dataclasses import dataclass
from typing import List
import os

from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv


@dataclass
class Listing:
    listing_id: int
    title: str
    quantity: int
    # url: str
    # views: int


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

    def get_all_inventory(self) -> List[Listing]:
        listings_endpoint_url = "https://openapi.etsy.com/v2/shops/wicksbywerby"
        session = self.create_etsy_session()
        raw_response = session.get(
            listings_endpoint_url, params={"includes": "Listings"}
        )
        items = raw_response.json()["results"][0]["Listings"]
        listings = [
            Listing(
                listing_id=item["listing_id"],
                title=item["title"],
                quantity=item["quantity"],
            )
            for item in items
            if item["state"] == "active"
        ]
        return listings


if __name__ == "__main__":
    load_dotenv()
    etsy = Etsy()
    etsy.get_all_inventory()
