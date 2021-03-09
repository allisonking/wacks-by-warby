import os

from dotenv import load_dotenv
import requests

TOM_NOOK_URL = "https://gonintendo.com/uploads/file_upload/upload/72974/wb.jpg"
DIMITRI_URL = "https://thumbs.gfycat.com/SardonicEveryHapuka-size_restricted.gif"


class Discord:
    def __init__(self) -> None:
        self.webhook = os.getenv("DISCORD_WEBHOOK")

    def send_message(self, sale_name: str, image_url: str):
        payload = {
            "username": "Wacks By Warby",
            "avatar_url": TOM_NOOK_URL,
            "content": f"🚨 New {sale_name} Sale! 🚨",
            "embeds": [{"image": {"url": image_url}}],
        }
        res = requests.post(self.webhook, json=payload)
        if res.status_code >= 400:
            print("status code", res.status_code)
            print(res.json())


if __name__ == "__main__":
    load_dotenv()
    d = Discord()
    d.send_message()
