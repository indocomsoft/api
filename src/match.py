def match_buyers_and_sellers(buy_orders, sell_orders, banned_user_matches):
    """
    The matching algorithm.

    Currently, this operates on the assumption that all securities passed in are the same.

    Params:
    buy_orders: e.g. [{'id': 'UUID', 'user_id': 'UUID', 'security_id': 'UUID',
                       'number_of_shares': 20.0, 'price': 30.0}]
    sell_orders: e.g. [{'id': 'UUID', 'user_id': 'UUID', 'security_id': 'UUID',
                        'number_of_shares': 20.0, 'price': 30.0}]
    banned_user_matches: users that cannot be matched together. Pass in enumerable of pairs.
    e.g. set(('buyer_uuid', 'seller_uuid'), ('buyer2_uuid', 'seller2_uuid'))

    Returns:
    Set of pairs of order IDs as matches.
    e.g. set(('buy_order_uuid', 'sell_order_uuid'),
             ('buy_order2_uuid', 'sell_order2_uuid'))
    """

    # TODO: This currently just matches all buy orders with sell orders.
    res = set()
    for sell_order in sell_orders:
        for buy_order in buy_orders:
            res.add((buy_order["id"], sell_order["id"]))

    return res
