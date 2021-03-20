import pytest

from wacksbywarby.wack import main
from wacksbywarby.db import Wackabase


@pytest.mark.parametrize(
    "changes, num_additional_sales, num_expected_discord_messages",
    [
        # None for num_additional_sales means we'll calculate a proper number
        ([], None, 0),
        ([("957749348", -1)], None, 1),
        ([("957749348", 1)], None, 0),
        ([("957749348", -1), ("943715197", -2)], None, 2),
        ([("957749348", 8), ("943715197", -2)], None, 1),
        # now pass in varying num_additional_sales for special cases
        ([("957749348", -5)], 0, 0),  # manual lowering of inventory
        ([("957749348", 5)], 0, 0),  # manual increase of inventory
    ],
)
def test_send_proper_number_of_messages(
    mocker,
    example_inventory,
    changed_inventory,
    changed_num_sales,
    changes,
    num_additional_sales,
    num_expected_discord_messages,
):
    new_inventory = changed_inventory(changes)
    previous_num_sales = 10
    new_num_sales = (
        changed_num_sales(changes, num_additional_sales) + previous_num_sales
    )

    # mock out the database
    mocker.patch(
        "wacksbywarby.db.Wackabase.get_last_entry", return_value=example_inventory
    )
    mocker.patch(
        "wacksbywarby.db.Wackabase.get_last_num_sales", return_value=previous_num_sales
    )
    mock_db = Wackabase("wacksbywarby/tests/data")

    # mock out the calls that tell us the current data
    mocker.patch(
        "wacksbywarby.wack.Etsy.get_inventory_state", return_value=new_inventory
    )
    mocker.patch(
        "wacksbywarby.wack.get_num_sales",
        return_value=new_num_sales,
    )

    # mock the discord message so we can count how many times it gets called
    mock_discord_message = mocker.patch("wacksbywarby.wack.Discord.send_sale_message")
    main(db=mock_db)
    assert mock_discord_message.call_count == num_expected_discord_messages


@pytest.mark.parametrize(
    "changes, num_additional_sales, num_inventory_writes",
    [
        # None for num_additional_sales means we'll calculate a proper number
        ([], None, 0),
        ([("957749348", -1)], None, 1),
        ([("957749348", 1)], None, 1),
        ([("957749348", -1), ("943715197", -2)], None, 1),
        ([("957749348", 8), ("943715197", -2)], None, 1),
        # now pass in varying num_additional_sales for special cases
        ([("957749348", -5)], 0, 1),  # manual lowering of inventory
        ([("957749348", 5)], 0, 1),  # manual increase of inventory
    ],
)
def test_write_inventory(
    mocker,
    example_inventory,
    changed_inventory,
    changed_num_sales,
    changes,
    num_additional_sales,
    num_inventory_writes,
):
    new_inventory = changed_inventory(changes)
    previous_num_sales = 10
    new_num_sales = (
        changed_num_sales(changes, num_additional_sales) + previous_num_sales
    )

    # mock out the database
    mocker.patch(
        "wacksbywarby.db.Wackabase.get_last_entry", return_value=example_inventory
    )
    mocker.patch(
        "wacksbywarby.db.Wackabase.get_last_num_sales", return_value=previous_num_sales
    )
    mock_inventory_write = mocker.patch("wacksbywarby.db.Wackabase.write_entry")
    mock_db = Wackabase("wacksbywarby/tests/data")

    # mock out the calls that tell us the current data
    mocker.patch(
        "wacksbywarby.wack.Etsy.get_inventory_state", return_value=new_inventory
    )
    mocker.patch(
        "wacksbywarby.wack.get_num_sales",
        return_value=new_num_sales,
    )

    main(db=mock_db)
    assert mock_inventory_write.call_count == num_inventory_writes
