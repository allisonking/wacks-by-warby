import argparse
import logging
import random
from datetime import datetime
from typing import List
from dataclasses import asdict

from dotenv import load_dotenv

from wacksbywarby.constants import WACK_ERROR_SENTINEL, SHIFT4SHOP_TIME_FORMAT
from wacksbywarby.db import Wackabase
from wacksbywarby.discord import Discord
from wacksbywarby.etsy import Etsy
from wacksbywarby.models import (
    DiscordEmbed,
    DiscordFooter,
    DiscordImage,
    Sale,
)
from wacksbywarby.scraper import get_num_sales as get_scraper_num_sales
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


def await_pizza_party(discord, num_sales):
    if num_sales == PARTY_NUM:
        logger.info("PARTY TIME")
        discord.send_party_message()


def main(db: Wackabase, dry=False):
    try:
        logger.info("TIME TO WACK")
        logger.info("Dry run: %s", dry)
        creds = db.get_etsy_creds()
        client = Etsy(credentials=creds, debug=dry)
        discord = Discord(debug=dry)

        last_timestamp = db.get_timestamp()
        if not last_timestamp:
            logger.error('No timestamp found for etsy')
            return
        last_timestamp_in_unix_seconds = int(datetime.strptime(
            last_timestamp, SHIFT4SHOP_TIME_FORMAT
        ).timestamp())
        sales = client.get_sales_since_timestamp(timestamp=last_timestamp_in_unix_seconds)
        if not sales:
            return

        logger.info(f"last timestamp was {last_timestamp}")

        last_num_sales = db.get_last_num_sales()
        if last_num_sales:
            current_num_sales = client.get_num_sales(
                last_timestamp=last_timestamp_in_unix_seconds, prev_num_sales=last_num_sales
            )
        else:
            # backfill using fallback
            current_num_sales = get_scraper_num_sales()

        logger.info(f"current num sales: {current_num_sales}")

        announce_new_sales(discord, sales, current_num_sales, id_type="etsy")
        await_pizza_party(discord, current_num_sales)

        # write out the most recent sale's date (results were sorted by created_at at desc, so latest one is first one)
        latest_sale_timestamp = sales[0].datetime
        if latest_sale_timestamp:
            db.write_timestamp(latest_sale_timestamp)
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
