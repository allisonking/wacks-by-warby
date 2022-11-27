import argparse
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from wacks4shop.shift4shop import Shift4Shop
from wacksbywarby.constants import WACK_ERROR_SENTINEL
from wacksbywarby.db import Wackabase
from wacksbywarby.discord import Discord
from wacksbywarby.wack import announce_new_sales, get_inventory_state_diff

DATABASE_DIR = "data/wacks4shop"

load_dotenv()

logger = logging.getLogger("wacks4shop")


def main(db: Wackabase, dry=False):
    try:
        logger.info("TIME TO WACK")
        logger.info("Dry run: %s", dry)

        discord = Discord(debug=dry)
        shift4shop = Shift4Shop(debug=dry)

        now = datetime.now()

        last_timestamp = db.get_timestamp()
        sales = shift4shop.determine_sales(timestamp=last_timestamp)

        if not sales:
            return

        # grab the current number of total sales
        previous_num_sales = db.get_last_num_sales()
        current_num_sales = shift4shop.get_num_sales()
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
            announce_new_sales(discord, sales, current_num_sales)

        db.write_timestamp(now)
        db.write_num_sales(current_num_sales)

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
