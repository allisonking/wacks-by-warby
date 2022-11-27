"""Helper script just to write the inventory out, no checks"""
from dotenv import load_dotenv
from wacksbywarby.db import Wackabase
from wacksbywarby.etsy import Etsy

if __name__ == "__main__":
    load_dotenv()
    etsy = Etsy()
    db = Wackabase()
    inventory = etsy.get_inventory_state()
    db.write_entry(inventory, pretty=True)
