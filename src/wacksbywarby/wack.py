import argparse
import logging
import os
import random
import time
from typing import List, Dict
from dataclasses import asdict

from dotenv import load_dotenv

from wacksbywarby.constants import WACK_ERROR_SENTINEL
from wacksbywarby.db import Wackabase
from wacksbywarby.discord import Discord
from wacksbywarby.etsy import Etsy
from wacksbywarby.models import (
    DiscordEmbed,
    DiscordFooter,
    DiscordImage,
    Inventory,
    InventoryDiff,
    Sale,
)
from wacksbywarby.scraper import get_num_sales
from wacksbywarby.werbies import IdType, Werbies

load_dotenv()

logger = logging.getLogger("wacksbywarby")

PARTY_NUM = 200


def announce_new_sales(
    discord: Discord, sales: List[Sale], num_total_sales: int, id_type: IdType = "etsy"
):
    """
    Format each sale as a Discord embed and post the message
    """
    embeds = []
    # figure out the images and name to show with the discord message
    for sale in sales:
        embed_data = Werbies.get_embed_data(sale.listing_id, id_type=id_type)
        if embed_data:
            image_urls = embed_data.images
            image_url = random.choice(image_urls)
            name = embed_data.name
            color = None
            if embed_data.color:
                # discord wants a decimal number for color
                color = int(embed_data.color.strip("#"), 16)
        else:
            # if there was any fallback info available about the sale use it, otherwise default to unknown
            name = sale.fallback_name if sale.fallback_name else "Unknown"
            image_url = ""
            color = None
        # format and send the discord message
        sold_out = sale.quantity == 0
        quantity_message = f" ({sale.num_sold:.0f} of 'em)" if sale.num_sold > 1 else ""
        location = f" [@{sale.location}]" if sale.location else ""
        message = f"🚨 New {name} Sale!{quantity_message}{location}🚨"
        embed = DiscordEmbed(
            title=message,
            image=DiscordImage(url=image_url),
            color=color,
            footer=None,
        )

        if sold_out:
            embed.footer = DiscordFooter(
                text="🙀 Hey this is sold out now! Werby we need you back at work!"
            )

        logger.info("listing id %s", sale.listing_id)
        logger.info("msg %s %s", message, image_url)
        embeds.append(embed)
    if embeds:
        embeds.append(
            DiscordEmbed(
                title=f"[{id_type}] {num_total_sales} total sales. Great job Werby! 🎉",
                color=15277667,  # LUMINOUS_VIVID_PINK
                footer=None,
                image=None,
            )
        )
        embeds_as_dict = [asdict(embed) for embed in embeds]
        discord.send_message(embeds_as_dict)


def transform_diffs_to_sales(id_to_listing_diff: Dict[str, InventoryDiff]):
    """
    Transform a dictionary of diffs into a list of sales
    """
    logger.info(f"{len(id_to_listing_diff)} differences!")
    i = 0

    # special code in the case of netteflix
    annette_id = "1083712348"
    felix_id = "1002448926"
    if id_to_listing_diff.get(annette_id) and id_to_listing_diff.get(felix_id):
        # it's netteflix!!
        logger.info("NETTEFLIX TIME")
        # hard code fake values that won't trigger a sold out msg
        id_to_listing_diff["netteflix"] = InventoryDiff(
            listing_id="netteflix",
            title="NETTEFLIX!!",
            prev_quantity=5,
            current_quantity=4,
        )
        id_to_listing_diff.pop(annette_id)
        id_to_listing_diff.pop(felix_id)
        i = 1

    sales = []
    for listing_id in id_to_listing_diff:
        listing = id_to_listing_diff[listing_id]
        prev_quantity = listing.prev_quantity
        current_quantity = listing.current_quantity

        # TODO: when quantity increases, skip for now
        if current_quantity > prev_quantity:
            logger.info(
                f"quantity increased from {prev_quantity} to {current_quantity} for {listing.title}"
            )
            i += 1
            continue

        # otherwise there's been a decrease in quantity, aka a sale!
        sales.append(
            Sale(
                listing_id=listing_id,
                quantity=current_quantity,
                num_sold=prev_quantity - current_quantity,
                datetime=None,
                location=None,
                fallback_name=listing.title
            )
        )
    return sales


def get_inventory_state_diff(
    previous_inventory: Dict[str, Inventory],
    current_inventory: Dict[str, Inventory],
) -> Dict[str, InventoryDiff]:
    if not previous_inventory:
        return {}

    state_diff = {}
    for listing_id in current_inventory:
        try:
            old_quantity = previous_inventory[listing_id].quantity
        except KeyError:
            # a new item has been added since we haven't seen it in previous inventories
            logger.info(f"listing id {listing_id} is new!")
            old_quantity = 0

        new_quantity = current_inventory[listing_id].quantity
        if new_quantity != old_quantity:
            state_diff[listing_id] = InventoryDiff(
                listing_id=listing_id,
                title=current_inventory[listing_id].title,
                prev_quantity=old_quantity,
                current_quantity=new_quantity,
            )
    logger.info("got inventory state diff, %s diffs", len(state_diff))
    logger.info(f"diffs: {state_diff}")
    return state_diff


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
        id_to_listing_diff = get_inventory_state_diff(
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
            sales = transform_diffs_to_sales(id_to_listing_diff)
            announce_new_sales(discord, sales, current_num_sales, id_type="etsy")
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
