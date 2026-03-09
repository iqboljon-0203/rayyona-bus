"""
JSON database manager for the bus booking bot.
All data is stored in data/db.json with atomic read/write operations.
"""

import json
import os
import threading
from datetime import datetime
from config import DB_PATH

_lock = threading.Lock()


def _load() -> dict:
    """Load the entire database from JSON file."""
    with _lock:
        if not os.path.exists(DB_PATH):
            return {}
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)


def _save(data: dict):
    """Save the entire database to JSON file (atomic write)."""
    with _lock:
        tmp_path = DB_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Atomic replace
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        os.rename(tmp_path, DB_PATH)


# ──────────────── Bot Info ────────────────

def get_bot_info() -> dict:
    return _load().get("bot_info", {})


def get_bus_photo_file_id() -> str | None:
    return _load().get("bot_info", {}).get("bus_photo_file_id")


def set_bus_photo_file_id(file_id: str):
    db = _load()
    if "bot_info" not in db:
        db["bot_info"] = {}
    db["bot_info"]["bus_photo_file_id"] = file_id
    _save(db)


# ──────────────── Directions, Sources & Cities ────────────────

def get_directions() -> list[dict]:
    """Get all main directions (e.g. UZ->RU, RU->UZ, KZ->RU)."""
    return _load().get("directions", [])


def get_direction(direction_id: str) -> dict | None:
    """Get a specific direction by ID."""
    for d in get_directions():
        if d["id"] == direction_id:
            return d
    return None


def get_sources(direction_id: str) -> list[dict]:
    """Get source cities (origins) for a given direction."""
    direction = get_direction(direction_id)
    if direction:
        return direction.get("sources", [])
    return []


def get_source(direction_id: str, source_name: str) -> dict | None:
    """Get a specific source for a given direction."""
    for s in get_sources(direction_id):
        if s["name"] == source_name:
            return s
    return None


def get_cities(direction_id: str, source_name: str) -> list[dict]:
    """Get destination cities for a specific source."""
    source = get_source(direction_id, source_name)
    if source:
        return source.get("cities", [])
    return []


def get_city(direction_id: str, source_name: str, city_name: str) -> dict | None:
    """Get a specific destination city."""
    for city in get_cities(direction_id, source_name):
        if city["name"] == city_name:
            return city
    return None


def update_price(direction_id: str, source_name: str, city_name: str, price_uzs: int, price_rub: int) -> bool:
    """Update price in DB based on hierarchy."""
    db = _load()
    for direction in db.get("directions", []):
        if direction["id"] == direction_id:
            for source in direction.get("sources", []):
                if source["name"] == source_name:
                    for city in source.get("cities", []):
                        if city["name"] == city_name:
                            city["price_uzs"] = price_uzs
                            city["price_rub"] = price_rub
                            _save(db)
                            return True
    return False


# ──────────────── Users ────────────────

def add_user(user_id: int, username: str = "", first_name: str = ""):
    db = _load()
    users = db.setdefault("users", [])
    for user in users:
        if user["user_id"] == user_id:
            user["username"] = username
            user["first_name"] = first_name
            user["last_seen"] = datetime.now().isoformat()
            _save(db)
            return

    users.append({
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "joined": datetime.now().isoformat(),
        "last_seen": datetime.now().isoformat()
    })
    _save(db)


def get_all_users() -> list[dict]:
    return _load().get("users", [])


def get_user_count() -> int:
    return len(get_all_users())


# ──────────────── Groups ────────────────

def add_group(group_id: int, title: str = ""):
    db = _load()
    groups = db.setdefault("groups", [])
    for group in groups:
        if group["group_id"] == group_id:
            group["title"] = title
            group["updated"] = datetime.now().isoformat()
            _save(db)
            return

    groups.append({
        "group_id": group_id,
        "title": title,
        "added": datetime.now().isoformat()
    })
    _save(db)


def remove_group(group_id: int):
    db = _load()
    groups = db.get("groups", [])
    db["groups"] = [g for g in groups if g["group_id"] != group_id]
    _save(db)


def get_all_groups() -> list[dict]:
    return _load().get("groups", [])


def get_group_count() -> int:
    return len(get_all_groups())


# ──────────────── Orders ────────────────

def add_order(
    user_id: int,
    username: str,
    first_name: str,
    direction_label: str,
    source_name: str,
    city_name: str,
    price_display: str,
    passenger_count: int,
    phone: str
) -> dict:
    db = _load()
    orders = db.setdefault("orders", [])
    
    order = {
        "id": len(orders) + 1,
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "direction": direction_label,
        "source": source_name,
        "city": city_name,
        "price_display": price_display,
        "passenger_count": passenger_count,
        "phone": phone,
        "created": datetime.now().isoformat(),
        "status": "new"
    }

    orders.append(order)
    _save(db)
    return order


def get_orders(limit: int = 20) -> list[dict]:
    db = _load()
    orders = db.get("orders", [])
    return list(reversed(orders[-limit:]))


def get_order_count() -> int:
    return len(_load().get("orders", []))


# ──────────────── Broadcast Campaigns ────────────────

def get_campaigns() -> list[dict]:
    return _load().get("campaigns", [])

def add_campaign(message_id: int, from_chat_id: int, interval_minutes: int = 60) -> dict:
    db = _load()
    camps = db.setdefault("campaigns", [])
    new_id = 1 if not camps else max(c["id"] for c in camps) + 1
    camp = {
        "id": new_id,
        "is_active": True,
        "interval_minutes": interval_minutes,
        "message_id": message_id,
        "from_chat_id": from_chat_id,
        "last_run": 0
    }
    camps.append(camp)
    _save(db)
    return camp

def update_campaign(camp_id: int, is_active: bool | None = None, interval_minutes: int | None = None, last_run: float | None = None) -> bool:
    db = _load()
    for c in db.get("campaigns", []):
        if c["id"] == camp_id:
            if is_active is not None:
                c["is_active"] = is_active
            if interval_minutes is not None:
                c["interval_minutes"] = interval_minutes
            if last_run is not None:
                c["last_run"] = last_run
            _save(db)
            return True
    return False

def delete_campaign(camp_id: int):
    db = _load()
    db["campaigns"] = [c for c in db.get("campaigns", []) if c["id"] != camp_id]
    _save(db)
