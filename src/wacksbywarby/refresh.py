import logging
import json
from datetime import datetime

from dotenv import load_dotenv

from wacksbywarby.etsy import Etsy
from wacksbywarby.db import Wackabase
from wacksbywarby.models import EtsyCredentials

load_dotenv()

logger = logging.getLogger("etsyrefresh")

ACCEPTABLE_MINUTES_UNTIL_REFRESH = 10


# this should run as a cronjob every 20 minutes or so so we have a chance to refresh the access_token which
# currently seems to expire every 3600 seconds (1 hour)
def main(db: Wackabase):
    logger.info("Checking if token refresh is needed...")
    creds = db.get_etsy_creds()

    # check if it is time to refresh
    expiration_date = creds.expires_at
    utcnow_in_seconds = int(datetime.utcnow().timestamp())
    minutes_until_expiration = (expiration_date - utcnow_in_seconds) / 60
    if minutes_until_expiration > ACCEPTABLE_MINUTES_UNTIL_REFRESH:
        return

    logger.info("Time to refresh! (expiration date was %s)", expiration_date)
    # request a new token from etsy
    client = Etsy(credentials=creds, debug=False)
    new_creds = client.refresh_access_token()
    if not new_creds:
        logger.error("Could not retrieve new token 🙀")
        return
    new_creds['expires_at'] = new_creds['expires_in'] + utcnow_in_seconds
    new_creds = EtsyCredentials.from_string(json.dumps(new_creds))

    # write the new token to the token file
    db.write_etsy_creds(new_creds)
    logger.info("Refresh succeeded 🎉")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    db = Wackabase()

    main(db)
