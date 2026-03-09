"""
Keyboard builders for the bus booking bot.
All inline and reply keyboards are defined here.
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
import database as db


# ──────────────── User Keyboards ────────────────

def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main menu: select direction (UZ->RU, RU->UZ, KZ->RU ...)."""
    directions = db.get_directions()
    buttons = []
    for d in directions:
        buttons.append([
            InlineKeyboardButton(
                text=d["label"],
                callback_data=f"dir:{d['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="📞 Bog'lanish", callback_data="contact_info")
    ])

    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="🛠 Adminka", callback_data="adm:menu")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sources_keyboard(direction_id: str) -> InlineKeyboardMarkup:
    """Origins/sources selection for a given direction."""
    sources = db.get_sources(direction_id)
    buttons = []

    for s in sources:
        buttons.append([
            InlineKeyboardButton(
                text=s['name'],
                callback_data=f"src:{direction_id}:{s['name']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="back:main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cities_keyboard(direction_id: str, source_name: str) -> InlineKeyboardMarkup:
    """City selection keyboard for a given direction and source."""
    cities = db.get_cities(direction_id, source_name)
    buttons = []

    # 2 cities per row
    row = []
    for i, city in enumerate(cities):
        row.append(
            InlineKeyboardButton(
                text=city['name'],
                callback_data=f"cty:{direction_id}:{source_name}:{city['name']}"
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Back button to sources
    buttons.append([
        InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"back:src:{direction_id}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def city_info_keyboard(direction_id: str, source_name: str, city_name: str) -> InlineKeyboardMarkup:
    """City info keyboard with booking and back buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📝 Bron qilish",
                callback_data=f"book:{direction_id}:{source_name}:{city_name}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Ortga",
                callback_data=f"back:cities:{direction_id}:{source_name}"
            )
        ]
    ])


def contact_share_keyboard() -> ReplyKeyboardMarkup:
    """Reply keyboard with contact share button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove the reply keyboard."""
    return ReplyKeyboardRemove()


# ──────────────── Admin Keyboards ────────────────

def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Narxlarni tahrirlash", callback_data="adm:prices")],
        [InlineKeyboardButton(text="📋 Buyurtmalar", callback_data="adm:orders")],
        [
            InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="adm:broadcast"),
            InlineKeyboardButton(text="⏱ Avto-reklama", callback_data="adm:ab_list")
        ],
        [InlineKeyboardButton(text="👥 Guruhlar", callback_data="adm:groups")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats")],
    ])


def admin_campaigns_keyboard(campaigns: list[dict]) -> InlineKeyboardMarkup:
    """Menu showing list of active campaigns."""
    buttons = []
    
    for c in campaigns:
        status = "🟢" if c["is_active"] else "🔴"
        has_msg = "✅" if c.get("message_id") else "❌"
        text = f"{status} Reklama #{c['id']} ({c['interval_minutes']} daq) {has_msg}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"adm_camp:{c['id']}")])
        
    buttons.append([InlineKeyboardButton(text="➕ Yangi reklama qo'shish", callback_data="adm_camp_add")])
    buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="adm:menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_single_campaign_keyboard(camp: dict) -> InlineKeyboardMarkup:
    """Menu for managing a specific auto-broadcast campaign."""
    buttons = []
    
    is_active = camp.get("is_active", False)
    interval = camp.get("interval_minutes", 60)
    has_msg = bool(camp.get("message_id"))
    
    status_text = "🔴 To'xtatish" if is_active else "🟢 Yoqish"
    msg_status = "✅ Sozlangan" if has_msg else "❌ Sozlanmagan"
    
    buttons.append([InlineKeyboardButton(text=f"✉️ Xabarni o'rnatish ({msg_status})", callback_data=f"adm_cp_msg:{camp['id']}")])
    buttons.append([InlineKeyboardButton(text=f"⏱ Taymer ({interval} daqiqa)", callback_data=f"adm_cp_time:{camp['id']}")])
    buttons.append([
        InlineKeyboardButton(text=status_text, callback_data=f"adm_cp_tg:{camp['id']}"),
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_cp_del:{camp['id']}")
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="adm:ab_list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_directions_keyboard() -> InlineKeyboardMarkup:
    directions = db.get_directions()
    buttons = []
    for d in directions:
        buttons.append([
            InlineKeyboardButton(
                text=d["label"],
                callback_data=f"adm_dir:{d['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="adm:menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_sources_keyboard(direction_id: str) -> InlineKeyboardMarkup:
    sources = db.get_sources(direction_id)
    buttons = []
    for s in sources:
        buttons.append([
            InlineKeyboardButton(
                text=s['name'],
                callback_data=f"adm_src:{direction_id}:{s['name']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ Ortga", callback_data="adm:prices")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_cities_keyboard(direction_id: str, source_name: str) -> InlineKeyboardMarkup:
    """City selection for admin price editing."""
    cities = db.get_cities(direction_id, source_name)
    buttons = []

    for city in cities:
        # Show only relevant currency if possible, or both
        price_text = f"{city['name']} — {city['price_uzs']:,} so'm / {city['price_rub']:,} ₽"
        buttons.append([
            InlineKeyboardButton(
                text=price_text,
                callback_data=f"adm_cty:{direction_id}:{source_name}:{city['name']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"adm_dir:{direction_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_back_keyboard() -> InlineKeyboardMarkup:
    """Simple back to admin menu button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="adm:menu")]
    ])
