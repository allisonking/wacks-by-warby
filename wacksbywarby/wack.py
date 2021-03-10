import argparse
import logging
import random

from dotenv import load_dotenv

from wacksbywarby.discord import Discord
from wacksbywarby.etsy import Etsy
from wacksbywarby.scraper import get_num_sales
from wacksbywarby.werbies import Werbies

logger = logging.getLogger("wacksbywarby")

PARTY_NUM = 100


def announce_new_sales(discord, id_to_listing_diff):
    logger.info(f"{len(id_to_listing_diff)} differences!")
    for listing_id in id_to_listing_diff:
        listing = id_to_listing_diff[listing_id]
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
        discord.send_sale_message(message, image_url)


def await_pizza_party(discord):
    logger.info("Getting num sales")
    try:
        num_sales = get_num_sales()
        logger.info(f"num sales={num_sales}")
        if num_sales >= PARTY_NUM:
            logger.info("PARTY TIME")
            discord.send_party_message()
    except Exception as e:
        logger.error(f"Error getting num sales: {e}")


def main(dry=False):
    logger.info("TIME TO WACK")
    load_dotenv()
    logger.info("Dry run: %s", dry)
    etsy = Etsy(debug=dry)
    discord = Discord(debug=dry)
    id_to_listing_diff = etsy.get_inventory_state_diff()
    if not id_to_listing_diff:
        return
    announce_new_sales(discord, id_to_listing_diff)
    etsy.write_inventory()
    await_pizza_party(discord)


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
