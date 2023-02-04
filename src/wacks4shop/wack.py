import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from wacks4shop.shift4shop import Shift4Shop
from wacksbywarby.constants import WACK_ERROR_SENTINEL
from wacksbywarby.db import Wackabase
from wacksbywarby.discord import Discord
from wacksbywarby.models import Sale
from wacksbywarby.wack import announce_new_sales

DATABASE_DIR = "data/wacks4shop"

load_dotenv()

logger = logging.getLogger("wacks4shop")


def main(db: Wackabase, dry=False):
    try:
        logger.info("TIME TO WACK")
        logger.debug("Dry run: %s", dry)

        discord = Discord(debug=dry)
        shift4shop = Shift4Shop(debug=dry)

        last_timestamp = db.get_timestamp()
        sales = shift4shop.determine_sales(timestamp=last_timestamp)
        if not sales:
            return

        # convert Shift4shop sales to Sales, purely for typing purposes, as
        # dataclasses in 3.9 don't handle inheritance super well, so announce_new_sales
        # doesn't know it's ok to take a Shift4Shop sale obj
        sales_to_announce = [
            Sale(listing_id=s.listing_id, quantity=s.quantity, num_sold=s.num_sold)
            for s in sales
        ]

        # grab the current number of total sales
        current_num_sales = shift4shop.get_num_sales()
        logger.info(f"current num sales: {current_num_sales}")
        announce_new_sales(
            discord, sales_to_announce, current_num_sales, id_type="shift4shop"
        )

        # write out the most recent sale's date
        latest_sale_time = sales[-1].datetime
        db.write_timestamp(latest_sale_time)

    except Exception as e:
        logger.error("%s: %s", WACK_ERROR_SENTINEL, e)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wacks4Shop!!")
    parser.add_argument(
        "--dry",
        action="store_true",
        required=False,
        help="run as dry run",
    )
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    args = parser.parse_args()

    # create the database folder if it doesn't exit
    Path(DATABASE_DIR).mkdir(parents=True, exist_ok=True)

    wackabase = Wackabase(DATABASE_DIR)
    main(db=wackabase, dry=args.dry)
    wackabase.write_success()
