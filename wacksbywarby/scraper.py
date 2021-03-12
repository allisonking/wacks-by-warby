import logging

import requests
from bs4 import BeautifulSoup

from wacksbywarby.constants import WACK_ERROR_SENTINEL

URL = "https://www.etsy.com/shop/WicksByWerby"
SOLD_HREF = "https://www.etsy.com/shop/WicksByWerby/sold"

logger = logging.getLogger("scraper")


def get_num_sales():
    try:
        logger.info("Getting num sales")
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        num_sales_tags = soup.find_all(href=SOLD_HREF)
        num_sales_text = num_sales_tags[0].text
        num_sales = int(num_sales_text.split(" ")[0])
        logger.info(f"num sales={num_sales}")
    except Exception as e:
        logger.error("%s Error getting num sales: %s", WACK_ERROR_SENTINEL, e)
        return None
    return num_sales
