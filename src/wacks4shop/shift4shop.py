import logging
import os

from wacksbywarby.models import Inventory

logger = logging.getLogger("shift4shop")


class Shift4Shop:
    def __init__(self, debug=False) -> None:
        self.key = os.getenv("SHIFT4SHOP_PRIVATE_KEY")
        self.shop_token = os.getenv("SHIFT4SHOP_SHOP_TOKEN")
        self.debug = debug

    def get_inventory_state(self) -> dict[str, Inventory]:
        # TODO
        return {}

    def get_num_sales(self) -> int:
        # TODO
        return 0
