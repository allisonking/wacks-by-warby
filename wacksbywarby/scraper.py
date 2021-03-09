import requests
from bs4 import BeautifulSoup

URL = "https://www.etsy.com/shop/WicksByWerby"
SOLD_HREF = "https://www.etsy.com/shop/WicksByWerby/sold"


def get_num_sales():
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    num_sales_tags = soup.find_all(href=SOLD_HREF)
    num_sales_text = num_sales_tags[0].text
    num_sales = int(num_sales_text.split(" ")[0])
    return num_sales
