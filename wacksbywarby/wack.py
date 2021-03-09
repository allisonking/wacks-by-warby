import argparse
import logging
import random

from dotenv import load_dotenv

from wacksbywarby.discord import Discord
from wacksbywarby.etsy import Etsy
from wacksbywarby.werbies import Werbies

logger = logging.getLogger("wacksbywarby")


def main(dry=False):
    logger.info("TIME TO WACK")
    load_dotenv()
    etsy = Etsy()
    discord = Discord()
    id_to_listing = etsy.get_inventory_state_diff()
    logger.info(f"{len(id_to_listing)} differences!")
    for listing_id in id_to_listing:
        listing = id_to_listing[listing_id]
        prev_quantity = listing["prev_quantity"]
        current_quantity = listing["current_quantity"]
        # TODO: when quantity increases
        if current_quantity > prev_quantity:
            continue
        embed_data = Werbies.get_embed_data(listing_id)
        if embed_data:
            image_urls = embed_data["images"]
            image_url = random.choice(image_urls)
            name = embed_data["name"]
        else:
            name = "Unknown"
            image_url = ""
        message = f"{prev_quantity - current_quantity} {name}"
        logger.info("listing id %s", listing_id)
        logger.info("msg %s %s", message, image_url)
        if not dry:
            discord.send_message(message, image_url)

    etsy.write_inventory()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wacks!!")
    parser.add_argument(
        "--dry",
        action="store_true",
        required=False,
        help="run as dry run",
    )
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    args = parser.parse_args()
    main(dry=args.dry)
