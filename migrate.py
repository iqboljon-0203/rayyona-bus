import json

db_path = "data/db.json"
with open(db_path, "r", encoding="utf-8") as f:
    db = json.load(f)

new_db = {
    "bot_info": db.get("bot_info", {}),
    "directions": [
        {
            "id": "uz_ru",
            "label": "🇺🇿 O'zbekistondan ➡️ 🇷🇺 Rossiyaga",
            "type": "uz_to_ru",
            "sources": [
                {
                    "name": "Toshkent",
                    "cities": [
                        {"name": "Moskva", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Sankt-Peterburg", "price_uzs": 1300000, "price_rub": 11000},
                        {"name": "Qozon", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Samara", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Vladimir", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Nijniy Novgorod", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Krasnodar", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Rostov-na-Donu", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Volgograd", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Saratov", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Novosibirsk", "price_uzs": 750000, "price_rub": 5000},
                        {"name": "Barnaul", "price_uzs": 750000, "price_rub": 5000},
                        {"name": "Perm", "price_uzs": 750000, "price_rub": 0},
                        {"name": "Ufa", "price_uzs": 750000, "price_rub": 0},
                        {"name": "Krasnoyarsk", "price_uzs": 1000000, "price_rub": 0},
                        {"name": "Ekaterinburg", "price_uzs": 850000, "price_rub": 0},
                        {"name": "Chelyabinsk", "price_uzs": 850000, "price_rub": 0},
                        {"name": "Irkutsk", "price_uzs": 1300000, "price_rub": 0},
                        {"name": "Tyumen", "price_uzs": 1000000, "price_rub": 0}
                    ]
                },
                {
                    "name": "Urganch",
                    "cities": [
                        {"name": "Moskva", "price_uzs": 1200000, "price_rub": 8500}
                    ]
                }
            ]
        },
        {
            "id": "ru_uz",
            "label": "🇷🇺 Rossiyadan ➡️ 🇺🇿 O'zbekistonga",
            "type": "ru_to_uz",
            "sources": [
                {
                    "name": "Toshkent",
                    "cities": [
                        {"name": "Moskva", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Sankt-Peterburg", "price_uzs": 1300000, "price_rub": 11000},
                        {"name": "Qozon", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Samara", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Vladimir", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Nijniy Novgorod", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Krasnodar", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Rostov-na-Donu", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Volgograd", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Saratov", "price_uzs": 1000000, "price_rub": 7000},
                        {"name": "Novosibirsk", "price_uzs": 750000, "price_rub": 5000},
                        {"name": "Barnaul", "price_uzs": 750000, "price_rub": 5000},
                        {"name": "Perm", "price_uzs": 750000, "price_rub": 0},
                        {"name": "Ufa", "price_uzs": 750000, "price_rub": 0},
                        {"name": "Krasnoyarsk", "price_uzs": 1000000, "price_rub": 0},
                        {"name": "Ekaterinburg", "price_uzs": 850000, "price_rub": 0},
                        {"name": "Chelyabinsk", "price_uzs": 850000, "price_rub": 0},
                        {"name": "Irkutsk", "price_uzs": 1300000, "price_rub": 0},
                        {"name": "Tyumen", "price_uzs": 1000000, "price_rub": 0}
                    ]
                },
                {
                    "name": "Urganch",
                    "cities": [
                        {"name": "Moskva", "price_uzs": 1200000, "price_rub": 8500}
                    ]
                }
            ]
        },
        {
            "id": "kz_ru",
            "label": "🇰🇿 Qozog'istondan ➡️ 🇷🇺 Rossiyaga",
            "type": "uz_to_ru",
            "sources": [
                {
                    "name": "Shymkent",
                    "cities": [
                        {"name": "Moskva", "price_uzs": 0, "price_rub": 6000}
                    ]
                }
            ]
        },
        {
            "id": "ru_kz",
            "label": "🇷🇺 Rossiyadan ➡️ 🇰🇿 Qozog'istonga",
            "type": "ru_to_uz",
            "sources": [
                {
                    "name": "Shymkent",
                    "cities": [
                        {"name": "Moskva", "price_uzs": 0, "price_rub": 7000}
                    ]
                }
            ]
        },
        {
            "id": "kg_ru",
            "label": "🇰🇬 Qirg'izistondan ➡️ 🇷🇺 Rossiyaga",
            "type": "uz_to_ru",
            "sources": [
                {
                    "name": "Bishkek",
                    "cities": [
                        {"name": "Moskva", "price_uzs": 0, "price_rub": 6000}
                    ]
                }
            ]
        },
        {
            "id": "ru_kg",
            "label": "🇷🇺 Rossiyadan ➡️ 🇰🇬 Qirg'izistonga",
            "type": "ru_to_uz",
            "sources": [
                {
                    "name": "Bishkek",
                    "cities": [
                        {"name": "Moskva", "price_uzs": 0, "price_rub": 7000}
                    ]
                }
            ]
        }
    ],
    "users": db.get("users", []),
    "groups": db.get("groups", []),
    "orders": db.get("orders", []),
    "contacts": db.get("contacts", {})
}

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(new_db, f, indent=2, ensure_ascii=False)
