import argparse
import logging
import random

from dotenv import load_dotenv

from wacksbywarby.constants import WACK_ERROR_SENTINEL
from wacksbywarby.db import Wackabase
from wacksbywarby.discord import Discord
from wacksbywarby.etsy import Etsy
from wacksbywarby.scraper import get_num_sales
from wacksbywarby.werbies import Werbies

load_dotenv()

logger = logging.getLogger("wacksbywarby")

PARTY_NUM = 200


def announce_new_sales(discord, id_to_listing_diff, num_total_sales):
    logger.info(f"{len(id_to_listing_diff)} differences!")
    num_sales = len(id_to_listing_diff)
    i = 0
    for listing_id in id_to_listing_diff:
        listing = id_to_listing_diff[listing_id]
        prev_quantity = listing["prev_quantity"]
        current_quantity = listing["current_quantity"]

        # TODO: when quantity increases, skip for now
        if current_quantity > prev_quantity:
            logger.info(
                f'quantity increased from {prev_quantity} to {current_quantity} for {listing["title"]}'
            )
            i += 1
            continue

        # otherwise there's been a decrease in quantity
        # figure out the images and name to show with the discord message
        embed_data = Werbies.get_embed_data(listing_id)
        if embed_data:
            image_urls = embed_data["images"]
            image_url = random.choice(image_urls)
            name = embed_data["name"]
        else:
            name = "Unknown"
            image_url = ""

        # format and send the discord message
        sold_out = current_quantity == 0
        num_sold = prev_quantity - current_quantity
        quantity_message = f" ({num_sold} of 'em)" if num_sold > 1 else ""
        message = f"🚨 New {name} Sale!{quantity_message} 🚨"
        footer = (
            f"{num_total_sales} total sales. Great job Werby!"
            if i == num_sales - 1
            else None
        )
        extra_embeds = []
        if sold_out:
            extra_embeds = [
                {"title": "Hey this is sold out now! Werby we need you back at work!"}
            ]
        logger.info("listing id %s", listing_id)
        logger.info("msg %s %s", message, image_url)
        discord.send_sale_message(
            message, image_url, footer=footer, extra_embeds=extra_embeds
        )
        i += 1


def await_pizza_party(discord, num_sales):
    if num_sales == PARTY_NUM:
        logger.info("PARTY TIME")
        discord.send_party_message()


def main(dry=False):
    try:
        logger.info("TIME TO WACK")
        logger.info("Dry run: %s", dry)
        etsy = Etsy(debug=dry)
        discord = Discord(debug=dry)
        wackabase = Wackabase()

        previous_inventory = wackabase.get_last_entry()
        current_inventory = etsy.get_inventory_state()
        id_to_listing_diff = etsy.get_inventory_state_diff(
            previous_inventory, current_inventory
        )
        if not id_to_listing_diff:
            return

        # grab the current number of total sales
        previous_num_sales = wackabase.get_last_num_sales()
        current_num_sales = get_num_sales()
        logger.info(
            f"current num sales: {current_num_sales}, previously stored num sales: {previous_num_sales}"
        )
        # handle the case where the shop owner manually lowers their own inventory
        # instead of inventory lowering coming from a sale
        if not current_num_sales > previous_num_sales:
            logger.info("num sales did not increase, skipping announcement")
        else:
            announce_new_sales(discord, id_to_listing_diff, current_num_sales)
            await_pizza_party(discord, current_num_sales)

        wackabase.write_entry(current_inventory)
        wackabase.write_num_sales(current_num_sales)

    except Exception as e:
        logger.error("%s: %s", WACK_ERROR_SENTINEL, e)
        raise


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
    Wackabase.write_success()
