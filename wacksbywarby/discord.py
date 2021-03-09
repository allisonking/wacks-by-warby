import os

from dotenv import load_dotenv
import requests

TOM_NOOK_URL = "https://gonintendo.com/uploads/file_upload/upload/72974/wb.jpg"
DIMITRI_URL = "https://thumbs.gfycat.com/SardonicEveryHapuka-size_restricted.gif"


class Discord:
    def __init__(self, debug=False) -> None:
        self.webhook = os.getenv("DISCORD_WEBHOOK")
        self.debug = debug

    def send_message(self, message):
        payload = {
            "username": "Wacks By Warby",
            "content": message,
        }
        self._make_request(payload)

    def send_sale_message(self, sale_name: str, image_url: str):
        payload = {
            "username": "Wacks By Warby",
            "avatar_url": TOM_NOOK_URL,
            "content": f"🚨 New {sale_name} Sale! 🚨",
            "embeds": [{"image": {"url": image_url}}],
        }
        self._make_request(payload)

    def _make_request(self, payload):
        if self.debug:
            return
        res = requests.post(self.webhook, json=payload)
        if res.status_code >= 400:
            print("status code", res.status_code)
            print(res.json())


if __name__ == "__main__":
    load_dotenv()
    d = Discord()
    d.send_sale_message()
