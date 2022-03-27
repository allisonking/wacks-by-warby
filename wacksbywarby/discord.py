import os

import requests
from dotenv import load_dotenv

TOM_NOOK_URL = "https://gonintendo.com/uploads/file_upload/upload/72974/wb.jpg"
CHEESE_KUN_URL = "https://pbs.twimg.com/media/DdsHM25U0AE7z8P?format=jpg&name=large"
PIZZA_IMAGE_URLS = [
    "https://chowhound3.cbsistatic.com/uploads/6/0/4/1355406_img_6065.jpg",
    "https://cdn.vox-cdn.com/uploads/chorus_image/image/65368949/IMG_1112.0.jpeg",
    "https://images.nycgo.com/image/fetch/q_70,w_900/https://www.nycgo.com/images/uploads/articles/Best_Pizza_Slice/Joes_Photo_Adam_Kuban.jpg",
    "https://infatuation.imgix.net/media/images/guides/best-pizza-nyc/NoahDevereaux_PizzaGuide_066_L%26B.JPG?auto=format&h=890&w=1336",
    "https://infatuation.imgix.net/media/images/guides/best-pizza-nyc/AdamFriedlander.NYC.FFPizza.BrownButterSagePie_2.jpg?auto=format&h=890&w=1336",
    "https://infatuation.imgix.net/media/images/guides/best-pizza-nyc/NitzanRubin_NYC_PaulieGeesSliceShop_Group_001.jpg?auto=format&h=890&w=1336",
    "https://media4.giphy.com/media/4ayiIWaq2VULC/200.gif",
    "https://media.tenor.com/images/fa644e962c59343d07265873dc5ab480/tenor.gif",
    "https://rachelhart.com/wp-content/uploads/2020/05/Ep100.jpg",
]
TWO_HUNDRED_SALES_AVATAR = "https://vanyaland.com/wp-content/uploads/2016/04/KeytarBearMarathon_CreditWeLoveKeytarBearFB.jpg"
BOSTON_IMAGE_URLS = [
    "http://yinandyolk.com/wp-content/uploads/2017/07/Area-Four-Cambridge-1024x683.jpg",
    "https://images.happycow.net/venues/1024/15/81/hcmp158127_578057.jpeg",
    "https://ap.rdcpix.com/6aa718a2d3c2bc6fd0f345c7c4290d80l-m965286925xd-w640_h480_q80.jpg",
    "https://ssl.cdn-redfin.com/photo/52/bigphoto/047/72619047_0.jpg",
    "https://d2787ndpv5cwhz.cloudfront.net/048590aa3701d37c8e46d13b368eaef8da2f2c7a/640x480.jpg",
    "https://i.makeagif.com/media/5-27-2015/-bTSyh.gif",
    "https://bostonglobe-prod.cdn.arcpublishing.com/resizer/aNGTraZfqMdx0hqd-KoK09fATOQ=/1440x0/cloudfront-us-east-1.images.arcpublishing.com/bostonglobe/DRPRJBRKFPPJAIWGOXKSJIMBYM.jpg",
    "https://newengland.com/wp-content/uploads/Chinatown-tour-1.jpg",
    "https://bostonglobe-prod.cdn.arcpublishing.com/resizer/Y6FBI4Vur93m-REZN2ckZVZJayw=/1440x0/arc-anglerfish-arc2-prod-bostonglobe.s3.amazonaws.com/public/2DP5CFVDGMI6TKM5KT3RK4TRNE.jpg",
    "https://charlesriverboat.com/wp-content/uploads/2019/08/Memorial-Drive-in-Fall.jpg",
]


class Discord:
    def __init__(self, debug=False) -> None:
        self.webhook = (
            os.getenv("DISCORD_DEBUG_WEBHOOK")
            if debug
            else os.getenv("DISCORD_WEBHOOK")
        )

    def send_healthcheck_message(self, message):
        payload = {
            "username": "Wacks By Warby",
            "content": message,
            "avatar_url": CHEESE_KUN_URL,
        }
        self._make_request(payload)

    def send_party_message(self):
        payload = {
            "username": "Wacks By Warby",
            "content": "TWO HUNDRED SALES!! TIME TO MOVE TO BOSTON",
            "avatar_url": TWO_HUNDRED_SALES_AVATAR,
            "embeds": [
                {"image": {"url": image_url}} for image_url in BOSTON_IMAGE_URLS
            ],
        }
        self._make_request(payload)

    def send_message(self, embeds):
        payload = {
            "username": "Wacks By Warby",
            "avatar_url": TOM_NOOK_URL,
            "embeds": embeds,
        }
        self._make_request(payload)

    def send_sale_message(
        self, message: str, image_url: str, footer=None, extra_embeds=None
    ):
        if extra_embeds is None:
            extra_embeds = []
        embed = {"image": {"url": image_url}}
        if footer is not None:
            embed["footer"] = {"text": footer}
        payload = {
            "username": "Wacks By Warby",
            "avatar_url": TOM_NOOK_URL,
            "content": message,
            "embeds": [embed] + extra_embeds,
        }
        self._make_request(payload)

    def _make_request(self, payload):
        print("request", payload)
        res = requests.post(self.webhook, json=payload)
        if res.status_code >= 400:
            print("status code", res.status_code)
            print(res.json())


if __name__ == "__main__":
    load_dotenv()
    d = Discord()
    d.send_sale_message()
