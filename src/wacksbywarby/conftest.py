"""Holds pytest fixture data"""

import json

import pytest
import requests

from wacksbywarby.discord import Discord
from wacksbywarby.models import Inventory


def read_sample_inventory() -> dict[str, Inventory]:
    with open("src/wacksbywarby/tests/fixtures/data.json", "r") as f:
        data = json.load(f)
        for key, value in data.items():
            data[key] = Inventory(
                listing_id=value["listing_id"],
                title=value["title"],
                quantity=value["quantity"],
                state=value["state"],
            )
        return data


@pytest.fixture
def example_inventory():
    return read_sample_inventory()


@pytest.fixture
def changed_inventory():
    """A fixture that alters the example_inventory with passed in changes

    Because of the way pytest fixtures work, we return this func that has arguments
    """

    def _change(changes):
        """
        changes: [(werbie_id, num_change)]
            i.e. [("1234", 4)] = 4 increase in item with id 1234
            i.e. [("1234", -1), ("5678", -1)] = 1 decrease in items 1234 and 5678
        """
        inventory = read_sample_inventory()
        for change in changes:
            werbie_id, num_change = change
            inventory[werbie_id].quantity = inventory[werbie_id].quantity + num_change
        return inventory

    return _change


@pytest.fixture
def changed_num_sales():
    def _change(changes, num_sales=None):
        """It's convenient to, given changes, just calculate the proper number
        of sales instead of having to figure it out while writing the tests.

        This func does that calculation to return the number of sales, but you
        can also just pass it a number of sales it will return which is convenient
        when trying to test when num_sales is not what you might expect
        """
        if num_sales is not None:
            return num_sales
        calculated_num_sales = 0
        for change in changes:
            _, num_change = change
            if num_change < 0:
                calculated_num_sales += abs(num_change)
        return calculated_num_sales

    return _change


@pytest.fixture(autouse=True)
def disable_send_discord_msg(monkeypatch):
    """We never want to send a discord message while running unit tests."""

    def pretend_msg():
        return

    monkeypatch.setattr(Discord, "_make_request", lambda *args, **kwargs: pretend_msg())


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    def stunted_get():
        raise RuntimeError("Network access not allowed during testing!")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get())
