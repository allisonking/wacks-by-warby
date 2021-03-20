import json

import pytest
import requests


def read_sample_inventory():
    with open("wacksbywarby/tests/fixtures/data.json", "r") as f:
        return json.load(f)


@pytest.fixture
def example_inventory():
    return read_sample_inventory()


@pytest.fixture
def changed_inventory():
    def _change(changes, num_sales=None):
        inventory = read_sample_inventory()
        for change in changes:
            werbie_id, num_change = change
            inventory[werbie_id]["quantity"] = (
                inventory[werbie_id]["quantity"] + num_change
            )
        return inventory

    return _change


@pytest.fixture
def changed_num_sales():
    def _change(changes, num_sales=None):
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
def disable_network_calls(monkeypatch):
    def stunted_get():
        raise RuntimeError("Network access not allowed during testing!")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get())