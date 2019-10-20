import pytest

from src.match import match_buyers_and_sellers

# fmt: off
TRIVIAL_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 5},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
    ],
    [],
    set([
        ("b1", "s1"),
    ]),
)

PERFECT_MATCHING_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "b2", "user_id": "X", "number_of_shares": 15, "price": 6},
        {"id": "b3", "user_id": "X", "number_of_shares": 30, "price": 7},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "s2", "user_id": "X", "number_of_shares": 15, "price": 6},
        {"id": "s3", "user_id": "X", "number_of_shares": 30, "price": 7},
    ],
    [],
    set([
        ("b1", "s1"),
        ("b2", "s2"),
        ("b3", "s3"),
    ]),
)

MATCH_TO_SAME_PRICE_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "b2", "user_id": "X", "number_of_shares": 200, "price": 6},
        {"id": "b3", "user_id": "X", "number_of_shares": 2000, "price": 7},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 2000, "price": 5},
        {"id": "s2", "user_id": "X", "number_of_shares": 200, "price": 6},
        {"id": "s3", "user_id": "X", "number_of_shares": 20, "price": 7},
    ],
    [],
    set([
        ("b1", "s1"),
        ("b2", "s2"),
        ("b3", "s3"),
    ]),
)

EXTRA_MATCHES_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "b2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "b3", "user_id": "X", "number_of_shares": 20, "price": 7},
        {"id": "b4", "user_id": "X", "number_of_shares": 20, "price": 8},
        {"id": "b5", "user_id": "X", "number_of_shares": 20, "price": 9},
        {"id": "b6", "user_id": "X", "number_of_shares": 20, "price": 10},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "s2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "s3", "user_id": "X", "number_of_shares": 20, "price": 7},
    ],
    [],
    set([
        # First matching
        ("b1", "s1"),
        ("b2", "s2"),
        ("b3", "s3"),
        # Match most desperate buyer to most desperate seller, etc.
        ("b6", "s1"),
        ("b5", "s2"),
        ("b4", "s3"),
    ]),
)

ONE_SELLER_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "b2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "b3", "user_id": "X", "number_of_shares": 20, "price": 7},
        {"id": "b4", "user_id": "X", "number_of_shares": 20, "price": 8},
        {"id": "b5", "user_id": "X", "number_of_shares": 20, "price": 9},
        {"id": "b6", "user_id": "X", "number_of_shares": 20, "price": 10},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
    ],
    [],
    set([
        ("b1", "s1"),
        ("b2", "s1"),
        ("b3", "s1"),
        ("b4", "s1"),
        ("b5", "s1"),
        ("b6", "s1"),
    ]),
)

ONE_BUYER_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 7},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "s2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "s3", "user_id": "X", "number_of_shares": 20, "price": 7},
        {"id": "s4", "user_id": "X", "number_of_shares": 20, "price": 8},
        {"id": "s5", "user_id": "X", "number_of_shares": 20, "price": 9},
        {"id": "s6", "user_id": "X", "number_of_shares": 20, "price": 10},
    ],
    [],
    set([
        # Note that each buyer is only matched with exactly one seller. In this case, the seller
        # that sets a price of 7 is lucky
        ("b1", "s3"),
    ]),
)

GET_TO_THE_NEAREST_NUMBER_OF_SHARES_ON_SAME_PRICE_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 15, "price": 5},
        {"id": "b2", "user_id": "X", "number_of_shares": 24, "price": 5},
        {"id": "b3", "user_id": "X", "number_of_shares": 25, "price": 6},
        {"id": "b4", "user_id": "X", "number_of_shares": 26, "price": 6},
        {"id": "b5", "user_id": "X", "number_of_shares": 15, "price": 7},
        {"id": "b6", "user_id": "X", "number_of_shares": 18, "price": 7},
        {"id": "b7", "user_id": "X", "number_of_shares": 18, "price": 8},
        {"id": "b8", "user_id": "X", "number_of_shares": 29, "price": 8},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "s2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "s3", "user_id": "X", "number_of_shares": 20, "price": 7},
        {"id": "s4", "user_id": "X", "number_of_shares": 20, "price": 8},
    ],
    [],
    set([
        # First matching, get the nearest number of shares if it is the same price level
        ("b2", "s1"),
        ("b3", "s2"),
        ("b6", "s3"),
        ("b7", "s4"),
        # Subsequent matches, most desperate to most desperate
        ("b8", "s1"),
        ("b5", "s2"),
        # Seller 3 and 4 does not get buyer 4 or 1 because of price constraints
        ("b4", "s1"),
        # Seller 2 does not get buyer 1 because of price constraints
        ("b1", "s1"),
    ]),
)

NO_SELLERS_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "b2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "b3", "user_id": "X", "number_of_shares": 20, "price": 7},
    ],
    [
    ],
    [],
    set([
    ]),
)

NO_BUYERS_CASE = (
    [
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "s2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "s3", "user_id": "X", "number_of_shares": 20, "price": 7},
    ],
    [],
    set([
    ]),
)

POPULATED_MARKET_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 4},
        {"id": "b2", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "b3", "user_id": "X", "number_of_shares": 30, "price": 5},
        {"id": "b4", "user_id": "X", "number_of_shares": 15, "price": 6},
        {"id": "b5", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "b6", "user_id": "X", "number_of_shares": 15, "price": 7},
        {"id": "b7", "user_id": "X", "number_of_shares": 22, "price": 7},
        {"id": "b8", "user_id": "X", "number_of_shares": 20, "price": 8},
        {"id": "b9", "user_id": "X", "number_of_shares": 20, "price": 9},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "s2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "s3", "user_id": "X", "number_of_shares": 20, "price": 7},
    ],
    [],
    set([
        # First matching
        ("b2", "s1"),
        ("b5", "s2"),
        ("b7", "s3"),
        # Subsequent matches, rolling
        ("b9", "s1"),
        ("b8", "s2"),
        ("b6", "s3"),
        ("b4", "s1"),
        ("b3", "s1"),
        # Seller 2 and seller 3 do not get anything else, because every other buy order has price
        # less than their price
    ]),
)

NEAREST_PRICE_BRACKET_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 4},
        {"id": "b2", "user_id": "X", "number_of_shares": 15, "price": 6},
        {"id": "b3", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "b4", "user_id": "X", "number_of_shares": 20, "price": 8},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "s2", "user_id": "X", "number_of_shares": 20, "price": 6},
        {"id": "s3", "user_id": "X", "number_of_shares": 20, "price": 7},
    ],
    [],
    set([
        # First matching. Make sure seller price < buyer price
        ("b2", "s1"),
        ("b3", "s2"),
        ("b4", "s3"),
        # No subsequent matches since b1's price is too low
    ]),
)

PRICE_MISMATCH_CASE = (
    [
        {"id": "b1", "user_id": "X", "number_of_shares": 20, "price": 4},
        {"id": "b2", "user_id": "X", "number_of_shares": 20, "price": 5},
        {"id": "b3", "user_id": "X", "number_of_shares": 20, "price": 6},
    ],
    [
        {"id": "s1", "user_id": "X", "number_of_shares": 20, "price": 7},
        {"id": "s2", "user_id": "X", "number_of_shares": 20, "price": 8},
        {"id": "s3", "user_id": "X", "number_of_shares": 20, "price": 9},
    ],
    [],
    set([
    ]),
)
# fmt: on

TEST_CASES = [
    TRIVIAL_CASE,
    PERFECT_MATCHING_CASE,
    MATCH_TO_SAME_PRICE_CASE,
    EXTRA_MATCHES_CASE,
    ONE_SELLER_CASE,
    ONE_BUYER_CASE,
    GET_TO_THE_NEAREST_NUMBER_OF_SHARES_ON_SAME_PRICE_CASE,
    NO_SELLERS_CASE,
    NO_BUYERS_CASE,
    POPULATED_MARKET_CASE,
    NEAREST_PRICE_BRACKET_CASE,
    PRICE_MISMATCH_CASE,
]


@pytest.mark.parametrize(
    "buy_orders,sell_orders,banned_user_matches,match_result", TEST_CASES
)
def test_match_buyers_and_sellers(
    buy_orders, sell_orders, banned_user_matches, match_result
):
    assert (
        match_buyers_and_sellers(buy_orders, sell_orders, banned_user_matches)
        == match_result
    )
