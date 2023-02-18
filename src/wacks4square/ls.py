import logging

from dotenv import load_dotenv

from wacks4square.square import Square

load_dotenv()

logger = logging.getLogger("wacks4shop")


def main():
    logger.info("Querying for products...")

    square = Square(debug=False)

    square.request_all_products()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    main()
