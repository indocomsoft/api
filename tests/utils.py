def assert_dict_in(inside, outside):
    for k, v in inside.items():
        assert v == outside[k]
