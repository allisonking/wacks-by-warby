import logging

from dotenv import load_dotenv

from wacksbywarby.discord import Discord
from wacksbywarby.wack import main

logger = logging.getLogger("healthcheck")

if __name__ == "__main__":
    try:
        load_dotenv()
        discord = Discord(debug=True)
        main(dry=True)
        discord.send_healthcheck_message("wack dry run successful")
        logger.info("Healthcheck successful")
    except Exception as e:
        logger.error("Healthcheck error %s", e)
        Discord(debug=True).send_healthcheck_message(
            f"Error occurred during dry run: {e}"
        )
