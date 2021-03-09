import logging
import random

from dotenv import load_dotenv

from wacksbywarby.discord import Discord
from wacksbywarby.etsy import Etsy
from wacksbywarby.werbies import Werbies

logger = logging.getLogger("wacksbywarby")


def main():
    logger.info("TIME TO WACK")
    load_dotenv()
    etsy = Etsy()
    discord = Discord()
    id_to_listing = etsy.get_inventory_state_diff()
    for listing_id in id_to_listing:
        listing = id_to_listing[listing_id]
        change_in_quantity = listing["change_in_quantity"]
        current_quantity = listing["current_quantity"]
        embed_data = Werbies.get_embed_data(listing_id)
        if embed_data:
            image_urls = embed_data["images"]
            image_url = random.choice(image_urls)
            name = embed_data["name"]
        else:
            name = "Unknown"
            image_url = ""
        message = f"{change_in_quantity} {name}"
        discord.send_message(message, image_url)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    main()
