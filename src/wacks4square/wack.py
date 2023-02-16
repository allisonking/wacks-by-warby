import argparse
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from filelock import FileLock, Timeout

from wacks4square.square import Square
from wacksbywarby.constants import SHIFT4SHOP_TIME_FORMAT, WACK_ERROR_SENTINEL
from wacksbywarby.db import Wackabase
from wacksbywarby.discord import Discord
from wacksbywarby.wack import announce_new_sales

DATABASE_DIR = "data/wack4square"
LOCKFILE = "wacks4quare.lock"

load_dotenv()

logger = logging.getLogger("wack4square")


def main(db: Wackabase, dry=False):
    try:
        logger.info("TIME TO WACK")
        logger.debug("Dry run: %s", dry)

        discord = Discord(debug=dry)
        square = Square(debug=dry)

        last_timestamp = db.get_timestamp()
        # stored in db with shift4shop format, but square requires RFC 3339 format so let's convert it
        if last_timestamp:
            last_timestamp = datetime.strptime(
                last_timestamp, SHIFT4SHOP_TIME_FORMAT
            ).isoformat()

        last_num_sales = db.get_last_num_sales()
        sales = square.get_sales_since_timestamp(timestamp=last_timestamp)
        if not sales:
            return

        logger.info(f"last timestamp was {last_timestamp}")

        # grab the current number of total sales
        if last_num_sales:
            current_num_sales = square.get_num_sales(
                last_timestamp=last_timestamp, prev_num_sales=last_num_sales
            )
        else:
            # backfill using slow method
            current_num_sales = square.get_num_sales_slow()

        logger.info(f"current num sales: {current_num_sales}")
        announce_new_sales(discord, sales, current_num_sales, id_type="square")

        # write out the most recent sale's date (results were sorted by closed at asc, so latest one is first one)
        latest_sale_timestamp = sales[0].datetime
        if latest_sale_timestamp:
            db.write_timestamp(latest_sale_timestamp)
            db.write_num_sales(current_num_sales)

    except Exception as e:
        logger.error("%s: %s", WACK_ERROR_SENTINEL, e)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wacks4Square!!")
    parser.add_argument(
        "--dry",
        action="store_true",
        required=False,
        help="run as dry run",
    )
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    args = parser.parse_args()

    # grab the lock
    try:
        lock = FileLock(LOCKFILE, timeout=5)
        with lock:
            # create the database folder if it doesn't exit
            Path(DATABASE_DIR).mkdir(parents=True, exist_ok=True)

            wackabase = Wackabase(DATABASE_DIR)
            main(db=wackabase, dry=args.dry)
            wackabase.write_success()
    except Timeout:
        logger.info("Could not acquire lock! Exiting.")
