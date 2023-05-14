import logging
import os
import secrets
import hashlib
import base64
import uuid
from datetime import datetime

import requests
from dotenv import load_dotenv
from wacksbywarby.models import Sale
from wacksbywarby.db import Wackabase

logger = logging.getLogger("etsy")


class Etsy:
    def __init__(self, credentials=None, debug=False) -> None:
        self.debug = debug
        self.shop_id = os.getenv("ETSY_SHOP_ID")
        self.v3_api_key = os.getenv("ETSY_V3_API_KEY")

        v3_access_token = credentials.access_token
        self.credentials = credentials
        self.headers = {
            'x-api-key': self.v3_api_key,
            'Authorization': f'Bearer {v3_access_token}'
        }

        # only need when getting initial access token for v3
        self.challenge_verifier = os.getenv('ETSY_CHALLENGE_VERIFIER')
        self.redirect_uri = os.getenv('ETSY_REDIRECT_URI')

    def _generate_challenge_verifier(self):
        # generate PKCE challenger verifier for etsy oauth which can be stored in env and re-used
        token_length = 44
        code_verifier = secrets.token_urlsafe(32)[:token_length]
        hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
        encoded = base64.urlsafe_b64encode(hashed)
        code_challenge = encoded.decode('ascii')[:-1]
        print('verifier', code_verifier, 'challenge', code_challenge)

    def make_oath_connect_request(self):
        """
        Make initial request to prompt Etsy account owner to grant permissions to our Etsy app.
        https://developers.etsy.com/documentation/essentials/authentication#step-1-request-an-authorization-code
        """
        connect_url = "https://www.etsy.com/oauth/connect"
        state = uuid.uuid4().hex
        hashed = hashlib.sha256(self.challenge_verifier.encode('ascii')).digest()
        encoded = base64.urlsafe_b64encode(hashed)
        code_challenge = encoded.decode('ascii')[:-1]
        # A URL-encoded, space-separated list of one or more scopes (e.g., shops_r%20shops_w)
        scopes = ' '.join(['listings_r', 'transactions_r'])
        # scopes = ' '.join(['transactions_r'])
        params = {
                "response_type": "code",
                "client_id": self.v3_api_key,
                "redirect_uri": self.redirect_uri,
                "scope": scopes,
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256"
            }
        raw_response = requests.get(connect_url, params=params)
        return raw_response.url

    def request_access_token(self, authorization_code=None):
        """
        Given authorization code from initial request, get a longer lived access token to use the V3 api
        https://developers.etsy.com/documentation/essentials/authentication#step-3-request-an-access-token
        """
        url = "https://api.etsy.com/v3/public/oauth/token"
        raw_response = requests.post(
            url, data={
                "grant_type": "authorization_code",
                "client_id": self.v3_api_key,
                "redirect_uri": self.redirect_uri,
                "code": authorization_code,
                "code_verifier": self.challenge_verifier
            }
        )
        response = raw_response.json()
        print(response)
        return response

    def refresh_access_token(self):
        """
        Given a refresh token, refreshes the expiration so we can continue using it as access_token to make requests
        https://developers.etsy.com/documentation/essentials/authentication#requesting-a-refresh-oauth-token
        """
        url = "https://api.etsy.com/v3/public/oauth/token"
        raw_response = requests.post(
            url, data={
                "grant_type": "refresh_token",
                "client_id": self.v3_api_key,
                "refresh_token": self.credentials.refresh_token
            }
        )
        response = raw_response.json()
        print(response)
        return response

    def _get_orders_since_timestamp(self, timestamp: int):
        logger.info(f"getting orders since timestamp, timestamp {timestamp}")
        url = f"https://api.etsy.com/v3/application/shops/{self.shop_id}/receipts"
        raw_response = requests.get(
            url,
            params={
                "client_id": self.v3_api_key,
                "sort_on": "created",
                # unix timestamp
                "min_created": timestamp,
                "limit": 100,
                "was_paid": "true",
                "is_canceled": "false",
            },
            headers=self.headers,
        )
        response = raw_response.json()
        orders = response.get('results', [])
        return orders

    def get_sales_since_timestamp(self, timestamp: int):
        """
        Get all the receipts which contain "transactions" or in other words, orders and line items within them.
        Convert them into Sale objects
        https://developers.etsy.com/documentation/reference/#operation/getShopReceipts
        """
        logger.info(f"getting sales since timestamp, timestamp {timestamp}")
        # bump timestamp to avoid re-fetching previous order
        orders = self._get_orders_since_timestamp(timestamp + 1)
        sales = []
        for order in orders:
            order_id = order.get("id")
            sale_time = order.get('created_timestamp')
            line_items = order.get("transactions", [])
            for item in line_items:
                listing_id = item.get("listing_id")
                fallback_name = item.get('title')
                if not listing_id:
                    logger.warning(f'no listing id found item: {item}, order_id: {order_id}')
                    continue
                try:
                    num_sold = int(item["quantity"])
                except ValueError as e:
                    logger.exception(
                        f"error converting quantity to int for order: {order}, item: {item}"
                    )
                    continue

                sale = Sale(
                    listing_id=str(listing_id),
                    num_sold=num_sold,
                    # TODO hardcode this for now since it seems like we need to make a new request to get the actual value
                    quantity=10,
                    datetime=datetime.fromtimestamp(sale_time),
                    fallback_name=fallback_name,
                    location=None
                )
                sales.append(sale)
        return sales

    def get_num_sales(self, last_timestamp: int, prev_num_sales: int) -> int:
        """
        Get total number of sales by using previously stored sales and timestamp and getting any new sales since
        then.
        """
        logger.info(
            f"getting num sales, last_timestamp {last_timestamp}, prev_num_sales: {prev_num_sales}"
        )
        new_orders_response = self._get_orders_since_timestamp(last_timestamp)
        num_new_orders = 0
        for order in new_orders_response:
            line_items = order.get("transactions", [])
            num_new_orders += len(line_items)
        num_total_sales = prev_num_sales + num_new_orders
        return num_total_sales


if __name__ == "__main__":
    load_dotenv()
    # do oauth
    db = Wackabase()
    creds = db.get_etsy_creds()
    client = Etsy(credentials=creds, debug=True)
    # one week ago
    client.get_sales_since_timestamp(timestamp=1682913600)


