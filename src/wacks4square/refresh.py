import logging
from datetime import datetime

from dotenv import load_dotenv

from wacks4square.constants import DATABASE_DIR
from wacks4square.square import Square
from wacksbywarby.db import Wackabase
from wacksbywarby.models import SquareCredentials

load_dotenv()

logger = logging.getLogger("wacks4square")

ACCEPTABLE_DAYS_UNTIL_REFRESH = 14


def main(db: Wackabase):
    logger.info("Checking if token refresh is needed...")
    creds = db.get_square_creds()

    # check if it is time to refresh
    expiration_date = creds.expires_at
    if (expiration_date - datetime.now()).days > ACCEPTABLE_DAYS_UNTIL_REFRESH:
        return

    logger.info("Time to refresh! (expiration date was %s)", expiration_date)
    # request a new token from square
    square = Square(credentials=creds, debug=False)
    new_token = square.request_token()
    if not new_token:
        logger.error("Could not retrieve new token 🙀")
        return
    new_creds = SquareCredentials.from_string(new_token)

    # write the new token to the token file
    db.write_square_creds(new_creds)
    logger.info("Refresh succeeded 🎉")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    db = Wackabase(DATABASE_DIR)

    main(db)
