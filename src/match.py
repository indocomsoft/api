def match_buyers_and_sellers(buy_orders, sell_orders, banned_user_matches):
    """
    The matching algorithm.

    Params:
    buy_orders: e.g. [{'id': 'UUID', 'user_id': 'UUID', 'security_id': 'UUID',
                       'number_of_shares': 20.0, 'price': 30.0}]
    sell_orders: e.g. [{'id': 'UUID', 'user_id': 'UUID', 'security_id': 'UUID',
                        'number_of_shares': 20.0, 'price': 30.0}]
    banned_user_matches: users that cannot be matched together. Pass in pair of tuples.
    e.g. [('buyer_uuid', 'seller_uuid'), ('buyer2_uuid', 'seller2_uuid')]

    Returns:
    Pair of tuples of order IDs as matches.
    e.g. [('buy_order_uuid', 'sell_order_uuid'),
          ('buy_order2_uuid', 'sell_order2_uuid')]
    """

    # TODO: This currently just matches all buy orders with sell orders.
    res = []
    for sell_order in sell_orders:
        for buy_order in buy_orders:
            res.append((buy_order.id, sell_order.id))

    return res
