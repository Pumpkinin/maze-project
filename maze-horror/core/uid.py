import uuid


def new_id(prefix="e"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"
