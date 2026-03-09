"""
User-facing handlers for the bus booking bot.
Handles: /start, direction selection, source, city selection, booking flow with FSM.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
import os

import database as db
from config import ADMIN_IDS, ORDERS_GROUP_ID
from keyboards.inline import (
    main_menu_keyboard,
    sources_keyboard,
    cities_keyboard,
    city_info_keyboard,
    contact_share_keyboard,
    remove_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()


# ──────────────── FSM States ────────────────

class BookingStates(StatesGroup):
    waiting_passenger_count = State()
    waiting_phone = State()


# ──────────────── /start Command ────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Welcome message and main menu."""
    await state.clear()

    # Register user
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or ""
    )

    welcome_text = (
        "🚌 <b>Rayyona Bus Xizmatiga Xush Kelibsiz!</b>\n\n"
        "Qulay va ishonchli avtobus sayohati uchun quyidagi yo'nalishlardan birini tanlang:\n\n"
        "⬇️ <b>Yo'nalishni tanlang:</b>"
    )

    is_admin = message.from_user.id in ADMIN_IDS

    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )


# ──────────────── Direction Selection ────────────────

@router.callback_query(F.data.startswith("dir:"))
async def on_direction_selected(callback: CallbackQuery, state: FSMContext):
    """User selected a direction (e.g., UZ->RU) — ask for source city (e.g. Toshkent or Urganch)."""
    await state.clear()
    parts = callback.data.split(":")
    direction_id = parts[1]
    
    direction = db.get_direction(direction_id)
    if not direction:
        await callback.answer("❌ Yo'nalish topilmadi", show_alert=True)
        return

    # E.g., uz_to_ru asks where you leave from, ru_to_uz asks where you go to.
    question = direction.get("sub_label", "Qaysi shaharni tanlaysiz?")
    if direction.get("type") == "uz_to_ru":
        question = "⬇️ Qaysi shahardan ketmoqchisiz?"
    else:
        question = "⬇️ Qaysi shaharga bormoqchisiz?"

    text = (
        f"🚌 <b>{direction['label']}</b>\n\n"
        f"{question}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=sources_keyboard(direction_id),
        parse_mode="HTML"
    )
    await callback.answer()

# ──────────────── Source Selection ────────────────

@router.callback_query(F.data.startswith("src:"))
async def on_source_selected(callback: CallbackQuery, state: FSMContext):
    """User selected a source city — show price list and destination buttons."""
    await state.clear()
    parts = callback.data.split(":")
    direction_id = parts[1]
    source_name = parts[2]

    direction = db.get_direction(direction_id)
    source = db.get_source(direction_id, source_name)

    if not direction or not source:
        await callback.answer("❌ Ma'lumot topilmadi", show_alert=True)
        return

    # Build price list
    cities = source.get("cities", [])
    price_lines = []
    
    for city in cities:
        # Construct route string and decide currency
        if direction.get("type") == "uz_to_ru":
            route = f"{source_name} → {city['name']}"
            price = f"{city['price_uzs']:,}".replace(",", " ")
            price_lines.append(f"  {route}\n  💵 {price} so'm\n")
        else:
            route = f"{city['name']} → {source_name}"
            price = f"{city['price_rub']:,}".replace(",", " ")
            price_lines.append(f"  {route}\n  💵 {price} ₽\n")

    prices_text = "\n".join(price_lines)

    if direction.get("type") == "uz_to_ru":
        q = "⬇️ Qaysi shaharga borasiz?"
    else:
        q = "⬇️ Qaysi shahardan ketasiz?"

    text = (
        f"🚌 <b>{direction['label']}</b>\n"
        f"📍 Tanlangan: <b>{source_name}</b>\n\n"
        f"━━━━━ 💰 NARXLAR ━━━━━\n\n"
        f"{prices_text}"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{q}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=cities_keyboard(direction_id, source_name),
        parse_mode="HTML"
    )
    await callback.answer()

# ──────────────── City Selection ────────────────

@router.callback_query(F.data.startswith("cty:"))
async def on_city_selected(callback: CallbackQuery, state: FSMContext):
    """User selected a specific destination/origin city — show detailed info & book option."""
    await state.clear()
    parts = callback.data.split(":")
    direction_id = parts[1]
    source_name = parts[2]
    city_name = parts[3]

    direction = db.get_direction(direction_id)
    city = db.get_city(direction_id, source_name, city_name)
    bot_info = db.get_bot_info()

    if not city or not direction:
        await callback.answer("❌ Ma'lumot topilmadi", show_alert=True)
        return

    # Format features
    features_text = "\n".join(bot_info.get("features", []))

    # Determine route name and price based on type
    if direction.get("type") == "uz_to_ru":
        route_name = f"{source_name} → {city_name}"
        price_display = f"{city['price_uzs']:,}".replace(",", " ") + " so'm"
        flag = "🇺🇿"
    else:
        route_name = f"{city_name} → {source_name}"
        price_display = f"{city['price_rub']:,}".replace(",", " ") + " rubl"
        flag = "🇷🇺"

    info_text = (
        f"🚌 <b>{route_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Narxi:</b>\n"
        f"┌─────────────────────┐\n"
        f"│  {flag}  <b>{price_display}</b>\n"
        f"└─────────────────────┘\n\n"
        f"🚍 <b>Avtobus:</b> {bot_info.get('bus_model', 'Yutong')} "
        f"({bot_info.get('capacity', 51)} o'rinlik)\n\n"
        f"<b>Afzalliklar:</b>\n{features_text}\n\n"
        f"📝 Bron qilish uchun quyidagi tugmani bosing:"
    )

    # Try to send bus photo with caption
    bus_photo_file_id = db.get_bus_photo_file_id()

    if bus_photo_file_id:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=bus_photo_file_id,
            caption=info_text,
            reply_markup=city_info_keyboard(direction_id, source_name, city_name),
            parse_mode="HTML"
        )
    else:
        # Check if local bus image exists
        bus_image_path = os.path.join(os.path.dirname(__file__), "..", "data", "bus.jpg")
        if os.path.exists(bus_image_path):
            try:
                await callback.message.delete()
            except Exception:
                pass
            sent_msg = await callback.message.answer_photo(
                photo=FSInputFile(bus_image_path),
                caption=info_text,
                reply_markup=city_info_keyboard(direction_id, source_name, city_name),
                parse_mode="HTML"
            )
            if sent_msg.photo:
                db.set_bus_photo_file_id(sent_msg.photo[-1].file_id)
        else:
            try:
                await callback.message.edit_text(
                    info_text,
                    reply_markup=city_info_keyboard(direction_id, source_name, city_name),
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.delete()
                await callback.message.answer(
                    info_text,
                    reply_markup=city_info_keyboard(direction_id, source_name, city_name),
                    parse_mode="HTML"
                )

    await callback.answer()


# ──────────────── Contact Info ────────────────

@router.callback_query(F.data == "contact_info")
async def on_contact_info(callback: CallbackQuery):
    """Show contact information."""
    contacts = db._load().get("contacts", {})
    text = (
        "📞 <b>Bog'lanish ma'lumotlari:</b>\n\n"
        f"🇺🇿 O'zbekiston: {contacts.get('phone_uz', 'Koʻrsatilmagan')}\n"
        f"🇷🇺 Rossiya: {contacts.get('phone_ru', 'Koʻrsatilmagan')}\n\n"
        f"🕐 Ish vaqti: {contacts.get('work_hours', '08:00 - 22:00')}\n\n"
        "Qo'shimcha savollar uchun qo'ng'iroq qiling!"
    )
    is_admin = callback.from_user.id in ADMIN_IDS

    try:
        await callback.message.edit_text(
            text,
            reply_markup=main_menu_keyboard(is_admin=is_admin),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text,
            reply_markup=main_menu_keyboard(is_admin=is_admin),
            parse_mode="HTML"
        )
    await callback.answer()


# ──────────────── Booking Flow ────────────────

@router.callback_query(F.data.startswith("book:"))
async def on_booking_start(callback: CallbackQuery, state: FSMContext):
    """Start booking — ask for passenger count."""
    parts = callback.data.split(":")
    direction_id = parts[1]
    source_name = parts[2]
    city_name = parts[3]

    direction = db.get_direction(direction_id)
    city = db.get_city(direction_id, source_name, city_name)

    if not direction or not city:
        await callback.answer("❌ Ma'lumot topilmadi", show_alert=True)
        return
        
    if direction.get("type") == "uz_to_ru":
        price_display = f"{city['price_uzs']:,}".replace(",", " ") + " so'm"
    else:
        price_display = f"{city['price_rub']:,}".replace(",", " ") + " ₽"

    # Save booking data to FSM
    await state.update_data(
        direction_id=direction_id,
        direction_label=direction["label"],
        source_name=source_name,
        city_name=city_name,
        price_display=price_display,
        type=direction.get("type", "uz_to_ru")
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "👥 <b>Necha kishi sayohat qiladi?</b>\n\n"
        "Yo'lovchilar sonini kiriting (raqam bilan):\n"
        "Masalan: <code>2</code>",
        parse_mode="HTML"
    )

    await state.set_state(BookingStates.waiting_passenger_count)
    await callback.answer()


@router.message(BookingStates.waiting_passenger_count)
async def on_passenger_count(message: Message, state: FSMContext):
    """Receive passenger count — ask for phone number."""

    text = message.text.strip() if message.text else ""
    if not text.isdigit() or int(text) < 1 or int(text) > 50:
        await message.answer(
            "⚠️ Iltimos, to'g'ri raqam kiriting (1 dan 50 gacha).\n"
            "Masalan: <code>2</code>",
            parse_mode="HTML"
        )
        return

    passenger_count = int(text)
    await state.update_data(passenger_count=passenger_count)

    await message.answer(
        "📱 <b>Telefon raqamingizni yuboring</b>\n\n"
        "Quyidagi tugma orqali telefon raqamingizni ulashing.\n"
        "Operator siz bilan bog'lanadi.",
        reply_markup=contact_share_keyboard(),
        parse_mode="HTML"
    )

    await state.set_state(BookingStates.waiting_phone)


@router.message(BookingStates.waiting_phone, F.contact)
async def on_contact_shared(message: Message, state: FSMContext):
    """Receive phone contact — save order and notify admin."""
    data = await state.get_data()
    phone = message.contact.phone_number

    # Save order to database
    order = db.add_order(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        direction_label=data["direction_label"],
        source_name=data["source_name"],
        city_name=data["city_name"],
        price_display=data["price_display"],
        passenger_count=data["passenger_count"],
        phone=phone
    )

    if data.get("type") == "uz_to_ru":
        route = f"{data['source_name']} → {data['city_name']}"
    else:
        route = f"{data['city_name']} → {data['source_name']}"

    confirm_text = (
        "✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"📍 {data['direction_label']}\n"
        f"🚌 Yo'nalish: {route}\n"
        f"👥 Yo'lovchilar: {data['passenger_count']} kishi\n"
        f"💰 Narx: {data['price_display']}\n"
        f"📱 Telefon: {phone}\n\n"
        "📞 <b>Operator tez orada siz bilan bog'lanadi!</b>\n\n"
        "Boshqa savollar uchun /start buyrug'ini bosing."
    )

    await message.answer(
        confirm_text,
        reply_markup=remove_keyboard(),
        parse_mode="HTML"
    )

    # Notify admins
    admin_text = (
        "🔔 <b>YANGI BUYURTMA!</b>\n\n"
        f"📍 {data['direction_label']}\n"
        f"🚌 Yo'nalish: {route}\n"
        f"👥 Yo'lovchilar: {data['passenger_count']} kishi\n"
        f"💰 Narx: {data['price_display']}\n\n"
        f"👤 Ism: {message.from_user.first_name or '—'}\n"
        f"🆔 Username: @{message.from_user.username or '—'}\n"
        f"📱 Telefon: {phone}\n"
        f"🕐 Buyurtma #{order['id']}"
    )

    # Notify group or admins
    target_chats = [ORDERS_GROUP_ID] if ORDERS_GROUP_ID else ADMIN_IDS

    for chat_id in target_chats:
        try:
            await message.bot.send_message(
                chat_id=chat_id,
                text=admin_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify order to chat {chat_id}: {e}")

    await state.clear()


@router.message(BookingStates.waiting_phone, F.text == "❌ Bekor qilish")
async def on_booking_cancel(message: Message, state: FSMContext):
    """Cancel booking."""
    await state.clear()
    await message.answer(
        "❌ Buyurtma bekor qilindi.\n\n"
        "Qaytadan boshlash uchun /start ni bosing.",
        reply_markup=remove_keyboard(),
        parse_mode="HTML"
    )


@router.message(BookingStates.waiting_phone)
async def on_waiting_phone_invalid(message: Message, state: FSMContext):
    """Handle invalid input during phone sharing state."""
    await message.answer(
        "⚠️ Iltimos, telefon raqamingizni quyidagi tugma orqali yuboring:",
        reply_markup=contact_share_keyboard(),
        parse_mode="HTML"
    )


# ──────────────── Back Navigation ────────────────

@router.callback_query(F.data == "back:main")
async def on_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Go back to main menu."""
    await state.clear()
    text = (
        "🚌 <b>Rayyona Bus Xizmati</b>\n\n"
        "⬇️ <b>Yo'nalishni tanlang:</b>"
    )
    is_admin = callback.from_user.id in ADMIN_IDS

    try:
        await callback.message.edit_text(
            text,
            reply_markup=main_menu_keyboard(is_admin=is_admin),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text,
            reply_markup=main_menu_keyboard(is_admin=is_admin),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("back:src:"))
async def on_back_to_sources(callback: CallbackQuery, state: FSMContext):
    """Go back to source/origin list."""
    await state.clear()
    direction_id = callback.data.split(":")[2]
    direction = db.get_direction(direction_id)

    if not direction:
        await callback.answer("❌ Xatolik", show_alert=True)
        return

    question = direction.get("sub_label", "Qaysi shaharni tanlaysiz?")
    if direction.get("type") == "uz_to_ru":
        question = "⬇️ Qaysi shahardan ketmoqchisiz?"
    else:
        question = "⬇️ Qaysi shaharga bormoqchisiz?"

    text = (
        f"🚌 <b>{direction['label']}</b>\n\n"
        f"{question}"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=sources_keyboard(direction_id),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text,
            reply_markup=sources_keyboard(direction_id),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("back:cities:"))
async def on_back_to_cities(callback: CallbackQuery, state: FSMContext):
    """Go back to city list."""
    await state.clear()
    parts = callback.data.split(":")
    direction_id = parts[2]
    source_name = parts[3]
    
    direction = db.get_direction(direction_id)
    source = db.get_source(direction_id, source_name)

    if not direction or not source:
        await callback.answer("❌ Xatolik", show_alert=True)
        return

    cities = source.get("cities", [])
    price_lines = []
    
    for city in cities:
        if direction.get("type") == "uz_to_ru":
            route = f"{source_name} → {city['name']}"
            price_lines.append(f"  {route}\n  💵 {city['price_uzs']:,}".replace(",", " ") + " so'm\n")
        else:
            route = f"{city['name']} → {source_name}"
            price_lines.append(f"  {route}\n  💵 {city['price_rub']:,}".replace(",", " ") + " ₽\n")

    prices_text = "\n".join(price_lines)

    if direction.get("type") == "uz_to_ru":
        q = "⬇️ Qaysi shaharga borasiz?"
    else:
        q = "⬇️ Qaysi shahardan ketasiz?"

    text = (
        f"🚌 <b>{direction['label']}</b>\n"
        f"📍 Tanlangan: <b>{source_name}</b>\n\n"
        f"━━━━━ 💰 NARXLAR ━━━━━\n\n"
        f"{prices_text}"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{q}"
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=cities_keyboard(direction_id, source_name),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text,
            reply_markup=cities_keyboard(direction_id, source_name),
            parse_mode="HTML"
        )
    await callback.answer()
