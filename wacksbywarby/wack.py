import logging
from dotenv import load_dotenv

from wacksbywarby.etsy import Etsy
from wacksbywarby.discord import Discord

logger = logging.getLogger("wacksbywarby")


def main():
    logger.info("TIME TO WACK")
    load_dotenv()
    etsy = Etsy()
    discord = Discord()
    # diff = etsy.get_diff()
    diff = [
        {"listing_id": "123", "change_in_quantity": -1, "quantity": 1},
        {"listing_id": "124", "change_in_quantity": 1, "quantity": 5},
    ]


if __name__ == "__main__":

    main()
