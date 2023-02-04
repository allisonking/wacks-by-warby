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

        discord = Discord(debug=dry)
        shift4shop = Shift4Shop(debug=dry)

        last_timestamp = db.get_timestamp()
        last_num_sales = db.get_last_num_sales()
        sales = shift4shop.determine_sales(timestamp=last_timestamp)
        if not sales:
            return

        # grab the currentr numbe of total sales
        current_num_sales = shift4shop.get_num_sales(timestamp=last_timestamp, prev_num_sales=last_num_sales)
        logger.info(f"current num sales: {current_num_sales}")
        announce_new_sales(discord, sales, current_num_sales, id_type="shift4shop")

        # write out the most recent sale's date
        latest_sale = sales[-1].datetime
        if latest_sale:
            db.write_timestamp(latest_sale)

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
