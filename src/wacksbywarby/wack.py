import argparse
import logging
import os
import random
import time

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


def announce_new_sales(discord: Discord, id_to_listing_diff, num_total_sales):
    logger.info(f"{len(id_to_listing_diff)} differences!")
    num_sales = len(id_to_listing_diff)
    i = 0

    # special code in the case of netteflix
    annette_id = "1083712348"
    felix_id = "1002448926"
    if id_to_listing_diff.get(annette_id) and id_to_listing_diff.get(felix_id):
        # it's netteflix!!
        logger.info("NETTEFLIX TIME")
        # hard code fake values that won't trigger a sold out msg
        id_to_listing_diff["netteflix"] = {
            "title": "NETTEFLIX!!",
            "prev_quantity": 5,
            "current_quantity": 4,
        }
        id_to_listing_diff.pop(annette_id)
        id_to_listing_diff.pop(felix_id)
        i = 1

    embeds = []
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
            color = embed_data.get("color")
            if color:
                # discord wants a decimal number for color
                color = int(color.strip("#"), 16)
        else:
            name = "Unknown"
            image_url = ""
            color = None
        # format and send the discord message
        sold_out = current_quantity == 0
        num_sold = prev_quantity - current_quantity
        quantity_message = f" ({num_sold} of 'em)" if num_sold > 1 else ""
        message = f"🚨 New {name} Sale!{quantity_message} 🚨"
        embed = {"title": message, "image": {"url": image_url}}
        # discord is finicky about colors
        if color:
            embed["color"] = color

        if sold_out:
            embed["footer"] = {
                "text": "🙀 Hey this is sold out now! Werby we need you back at work!"
            }

        logger.info("listing id %s", listing_id)
        logger.info("msg %s %s", message, image_url)
        embeds.append(embed)
    if embeds:
        embeds.append(
            {
                "title": f"{num_total_sales} total sales. Great job Werby! 🎉",
                "color": 15277667,  # LUMINOUS_VIVID_PINK
            }
        )
        discord.send_message(embeds)


def await_pizza_party(discord, num_sales):
    if num_sales == PARTY_NUM:
        logger.info("PARTY TIME")
        discord.send_party_message()


def delay(dry):
    skip_sleep = dry or "PYTEST_CURRENT_TEST" in os.environ
    if not skip_sleep:
        time.sleep(15)


def main(db: Wackabase, dry=False):
    try:
        logger.info("TIME TO WACK")
        logger.info("Dry run: %s", dry)
        etsy = Etsy(debug=dry)
        discord = Discord(debug=dry)

        previous_inventory = db.get_last_entry()
        current_inventory = etsy.get_inventory_state()
        id_to_listing_diff = etsy.get_inventory_state_diff(
            previous_inventory, current_inventory
        )
        if not id_to_listing_diff:
            return

        # grab the current number of total sales
        # sometimes the etsy page is slow to update sale_num though, so we sleep to give it some time
        delay(dry)

        previous_num_sales = db.get_last_num_sales()
        current_num_sales = get_num_sales()
        logger.info(
            f"current num sales: {current_num_sales}, previously stored num sales: {previous_num_sales}"
        )
        # handle the case where the shop owner manually lowers their own inventory
        # instead of inventory lowering coming from a sale
        if not current_num_sales > previous_num_sales:
            logger.info(
                "num sales did not increase, skipping announcement (%d --> %d)",
                current_num_sales,
                previous_num_sales,
            )
        else:
            announce_new_sales(discord, id_to_listing_diff, current_num_sales)
            await_pizza_party(discord, current_num_sales)

        db.write_entry(current_inventory, pretty=True)
        db.write_num_sales(current_num_sales)

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
    wackabase = Wackabase()
    main(db=wackabase, dry=args.dry)
    wackabase.write_success()
