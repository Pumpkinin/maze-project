"""JSON-сериализация с версией схемы и мягким откатом на старый формат."""
import json
import os

SCHEMA_VERSION = 1


def save_json(path, data, schema=SCHEMA_VERSION):
    payload = {"__schema__": schema, "data": data}
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict) and "__schema__" in payload:
        return payload["data"]
    return payload
