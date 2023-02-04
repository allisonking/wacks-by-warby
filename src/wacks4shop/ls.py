import logging

from dotenv import load_dotenv

from wacks4shop.shift4shop import Shift4Shop

load_dotenv()

logger = logging.getLogger("wacks4shop")


def main():
    logger.info("Querying for products...")

    shift4shop = Shift4Shop(debug=False)

    products = shift4shop.request_all_products()
    for product in products:
        catalog_id = product["SKUInfo"]["CatalogID"]
        name = product["SKUInfo"]["Name"]
        logger.info(f"{catalog_id}: {name}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    main()
