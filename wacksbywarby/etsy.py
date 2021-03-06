from typing import Mapping
import os

import requests
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv


class Etsy:
    def __init__(self) -> None:

        self.key = os.getenv("ETSY_API_KEY")
        self.secret = os.getenv("ETSY_SECRET")
        self.request_token_url = "https://openapi.etsy.com/v2/oauth/request_token"
        self.url = "https://openapi.etsy.com/v2/listings/active"
        self.shop_name = "wicksbywerby"

    def oauth(self):
        oauth = OAuth1Session(self.key, self.secret)
        fetch_response = oauth.fetch_request_token(
            self.request_token_url, data={"scope": "transactions_r"}
        )
        print(fetch_response)


if __name__ == "__main__":
    load_dotenv()
    etsy = Etsy()
    etsy.oauth()
