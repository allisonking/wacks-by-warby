import logging

from dotenv import load_dotenv

from wacksbywarby.discord import Discord
from wacksbywarby.wack import main


logger = logging.getLogger("healthcheck")

if __name__ == "__main__":
    load_dotenv()
    try:
        logger.info("starting health check...")
        discord = Discord(debug=True)
        main(dry=True)
        discord.send_healthcheck_message("wack health check succeeded")
        logger.info("healthcheck successful")
    except Exception as e:
        logger.error("healthcheck error %s", e)
        Discord(debug=True).send_healthcheck_message(
            f"Error occurred during wack health check: {e}"
        )
