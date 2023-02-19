import logging

from dotenv import load_dotenv

from wacks4square.constants import DATABASE_DIR
from wacks4square.square import Square
from wacksbywarby.db import Wackabase

load_dotenv()

logger = logging.getLogger("wacks4square")


def main(db: Wackabase):
    logger.info("Querying for products...")
    creds = db.get_square_creds()
    square = Square(credentials=creds, debug=False)

    square.request_all_products()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    wackabase = Wackabase(DATABASE_DIR)

    main(wackabase)
