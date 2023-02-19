import logging

from dotenv import load_dotenv

from wacks4square.square import Square

load_dotenv()

logger = logging.getLogger("wacks4shop")


def main():
    logger.info("Checking if token refresh is needed...")
    # TODO: read in the existing token file and check if the expiration is under a week away

    # if it is not, exit here

    # if it is, request a new token from Square
    square = Square(debug=False)
    # new_token = square.refresh_token

    # write the new token to the token file


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    main()
