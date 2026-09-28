"""Конфиг редактора: последний проект и список недавних.

Хранится в ~/.maze-studio/config.json. Ничего не пишет в репозиторий.
"""
import json
import os

CONFIG_DIR = os.path.expanduser("~/.maze-studio")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
MAX_RECENT = 10


def _default():
    return {"last_project": None, "recent_projects": []}


def load_config():
    if not os.path.isfile(CONFIG_PATH):
        return _default()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _default()
        data.setdefault("last_project", None)
        data.setdefault("recent_projects", [])
        return data
    except Exception:
        return _default()


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def remember_project(path):
    cfg = load_config()
    path = os.path.abspath(path)
    cfg["last_project"] = path
    rec = [p for p in cfg.get("recent_projects", []) if p != path]
    rec.insert(0, path)
    cfg["recent_projects"] = rec[:MAX_RECENT]
    save_config(cfg)
    return cfg


def get_last_project():
    return load_config().get("last_project")


def get_recent_projects():
    return list(load_config().get("recent_projects", []))
