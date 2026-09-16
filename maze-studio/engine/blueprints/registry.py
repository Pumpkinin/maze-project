NODE_TYPES = {}


def register(cls):
    NODE_TYPES[cls.type_name] = cls
    return cls


def get(type_name):
    return NODE_TYPES.get(type_name)


def all_types():
    return dict(NODE_TYPES)
