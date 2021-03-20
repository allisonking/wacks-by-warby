import pytest

from wacksbywarby.wack import main


@pytest.mark.parametrize(
    "changes, num_expected_discord_messages",
    [
        ([], 0),
        ([("957749348", -1)], 1),
        ([("957749348", 1)], 0),
        ([("957749348", -1), ("943715197", -2)], 2),
        ([("957749348", 8), ("943715197", -2)], 1),
    ],
)
def test_send_proper_number_of_messages(
    mocker,
    example_inventory,
    changed_inventory,
    changed_num_sales,
    changes,
    num_expected_discord_messages,
):
    new_inventory = changed_inventory(changes)
    previous_num_sales = 10
    new_num_sales = changed_num_sales(changes) + previous_num_sales
    # patch all the previous and next states
    mocker.patch(
        "wacksbywarby.wack.Wackabase.get_last_entry", return_value=example_inventory
    )
    mocker.patch(
        "wacksbywarby.wack.Etsy.get_inventory_state", return_value=new_inventory
    )
    mocker.patch(
        "wacksbywarby.wack.Wackabase.get_last_num_sales",
        return_value=previous_num_sales,
    )
    mocker.patch(
        "wacksbywarby.wack.get_num_sales",
        return_value=new_num_sales,
    )

    # mock the discord message so we can count how many times it gets called
    mock_discord_message = mocker.patch("wacksbywarby.wack.Discord.send_sale_message")
    main()
    assert mock_discord_message.call_count == num_expected_discord_messages
