"""
Admin panel handlers.
Handles: /admin menu, editing prices (with FSM), viewing orders, statistics, broadcasting.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

import database as db
from config import ADMIN_IDS, BROADCAST_DELAY, ORDERS_GROUP_ID
from keyboards.inline import (
    admin_menu_keyboard,
    admin_directions_keyboard,
    admin_sources_keyboard,
    admin_cities_keyboard,
    admin_back_keyboard,
    admin_campaigns_keyboard,
    admin_single_campaign_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()


class AdminStates(StatesGroup):
    waiting_new_price_uzs = State()
    waiting_new_price_rub = State()
    waiting_broadcast_message = State()
    
    waiting_cp_message = State()
    waiting_cp_interval = State()
    
    waiting_new_cp_msg = State()
    waiting_new_cp_interval = State()


# ──────────────── Admin Filter ────────────────
filter_admin = F.from_user.id.in_(ADMIN_IDS)


# ──────────────── /admin Command ────────────────

@router.message(Command("admin"), filter_admin)
async def cmd_admin(message: Message, state: FSMContext):
    """Open admin panel."""
    await state.clear()
    await message.answer(
        "🛠 <b>Admin panelga xush kelibsiz!</b>\n\nQuyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


# ──────────────── Admin Menu Navigation ────────────────

@router.callback_query(F.data == "adm:menu", filter_admin)
async def on_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Go back to admin main menu."""
    await state.clear()
    await callback.message.edit_text(
        "🛠 <b>Admin panelga xush kelibsiz!</b>\n\nQuyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ──────────────── Price Editing Flow ────────────────

@router.callback_query(F.data == "adm:prices", filter_admin)
async def on_admin_prices_menu(callback: CallbackQuery, state: FSMContext):
    """Show directions for price editing."""
    await state.clear()
    await callback.message.edit_text(
        "📝 <b>Qaysi yo'nalish narxini o'zgartirmoqchisiz?</b>\n\nYo'nalishni tanlang:",
        reply_markup=admin_directions_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_dir:"), filter_admin)
async def on_admin_direction_selected(callback: CallbackQuery):
    """Show sources (e.g. Toshkent, Urganch) for a selected direction."""
    direction_id = callback.data.split(":")[1]
    direction = db.get_direction(direction_id)
    if not direction:
        await callback.answer("❌ Yo'nalish topilmadi", show_alert=True)
        return

    await callback.message.edit_text(
        f"📝 <b>{direction['label']}</b>\n\nQaysi shahardan (yoki shaharga):",
        reply_markup=admin_sources_keyboard(direction_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_src:"), filter_admin)
async def on_admin_source_selected(callback: CallbackQuery):
    """Show cities for a selected source."""
    parts = callback.data.split(":")
    direction_id = parts[1]
    source_name = parts[2]
    
    direction = db.get_direction(direction_id)
    if not direction:
        await callback.answer("❌ Yo'nalish topilmadi", show_alert=True)
        return

    await callback.message.edit_text(
        f"📝 <b>{direction['label']}</b>\n"
        f"📍 {source_name}\n\n"
        f"Qaysi shahar narxini o'zgartirmoqchisiz?",
        reply_markup=admin_cities_keyboard(direction_id, source_name),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_cty:"), filter_admin)
async def on_admin_city_selected(callback: CallbackQuery, state: FSMContext):
    """Ask for new UZS price."""
    parts = callback.data.split(":")
    direction_id = parts[1]
    source_name = parts[2]
    city_name = parts[3]

    city = db.get_city(direction_id, source_name, city_name)
    if not city:
        await callback.answer("❌ Shahar topilmadi", show_alert=True)
        return

    await state.update_data(
        direction_id=direction_id,
        source_name=source_name,
        city_name=city_name,
        current_uzs=city["price_uzs"],
        current_rub=city["price_rub"]
    )

    await callback.message.edit_text(
        f"📍 <b>{city_name}</b> narxini o'zgartirish.\n\n"
        f"Joriy narxlar:\n"
        f"🇺🇿 {city['price_uzs']:,} so'm\n"
        f"🇷🇺 {city['price_rub']:,} rubl\n\n"
        f"✏️ <b>Yangi so'm narxini yuboring:</b> (faqat raqam)",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_new_price_uzs)
    await callback.answer()


@router.message(AdminStates.waiting_new_price_uzs, filter_admin)
async def on_new_price_uzs(message: Message, state: FSMContext):
    """Receive new UZS price, ask for new RUB price."""
    text = message.text.replace(" ", "")
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqam kiriting!")
        return

    new_uzs = int(text)
    await state.update_data(new_uzs=new_uzs)

    await message.answer(
        f"✅ So'm narxi qabul qilindi: <b>{new_uzs:,}</b> so'm\n\n"
        f"✏️ Endi <b>rubl narxini</b> yuboring: (faqat raqam)",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_new_price_rub)


@router.message(AdminStates.waiting_new_price_rub, filter_admin)
async def on_new_price_rub(message: Message, state: FSMContext):
    """Receive new RUB price, update DB."""
    text = message.text.replace(" ", "")
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqam kiriting!")
        return

    new_rub = int(text)
    data = await state.get_data()
    direction_id = data["direction_id"]
    source_name = data["source_name"]
    city_name = data["city_name"]
    new_uzs = data["new_uzs"]

    # Update DB
    success = db.update_price(
        direction_id=direction_id,
        source_name=source_name,
        city_name=city_name,
        price_uzs=new_uzs,
        price_rub=new_rub
    )

    if success:
        await message.answer(
            f"✅ <b>{city_name}</b> uchun narxlar muvaffaqiyatli yangilandi!\n\n"
            f"🇺🇿 Yangi narx: {new_uzs:,} so'm\n"
            f"🇷🇺 Yangi narx: {new_rub:,} rubl",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")

    await state.clear()


# ──────────────── View Orders ────────────────

@router.callback_query(F.data == "adm:orders", filter_admin)
async def on_admin_orders(callback: CallbackQuery):
    """Show last 10 orders."""
    orders = db.get_orders(limit=10)

    if not orders:
        await callback.message.edit_text(
            "📭 Hozircha buyurtmalar yo'q.",
            reply_markup=admin_back_keyboard()
        )
        return

    text = "📋 <b>Oxirgi 10 ta buyurtma:</b>\n\n"
    for o in orders:
        if "source" in o:
            if "O'zbekistondan" in o.get('direction', ''):
                route = f"{o['source']} ➡️ {o['city']}"
            else:
                route = f"{o['city']} ➡️ {o['source']}"
        else:
            route = o['city']
            
        phone = o.get('phone', "Ko'rsatilmagan")
        text += (
            f"🛒 <b>Buyurtma #{o['id']}</b>\n"
            f"🚌 <b>Marshrut:</b> {route}\n"
            f"👥 <b>Yo'lovchilar:</b> {o['passenger_count']} kishi\n"
            f"👤 <b>Mijoz:</b> {o['first_name']}\n"
            f"📞 <b>Telefon:</b> {phone}\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ──────────────── Groups ────────────────

@router.callback_query(F.data == "adm:groups", filter_admin)
async def on_admin_groups(callback: CallbackQuery):
    """View registered groups."""
    groups = db.get_all_groups()

    if not groups:
        await callback.message.edit_text(
            "📭 Hozircha bot tarkibiga guruhlar biriktirilmagan.",
            reply_markup=admin_back_keyboard(),
            parse_mode="HTML"
        )
        return

    text = f"👥 <b>Ullangan guruhlar ({len(groups)} ta)</b>\n\n"
    for g in groups:
        title = g.get('title', 'Nomsiz guruh')
        # Clean title to avoid HTML tags issues:
        title = title.replace('<', '&lt;').replace('>', '&gt;')
        date = g.get('added', 'Noaniq').split('T')[0]
        text += f"▪️ <b>{title}</b>\n"
        text += f"   ID: <code>{g['group_id']}</code>\n"
        text += f"   Sana: {date}\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ──────────────── Statistics ────────────────

@router.callback_query(F.data == "adm:stats", filter_admin)
async def on_admin_stats(callback: CallbackQuery):
    """Show basic bot statistics."""
    user_count = db.get_user_count()
    group_count = db.get_group_count()
    order_count = db.get_order_count()

    text = (
        "📊 <b>Bot Statistikasi:</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{user_count}</b> ta\n"
        f"👥 Guruhlar: <b>{group_count}</b> ta\n"
        f"📦 Jami buyurtmalar: <b>{order_count}</b> ta\n"
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ──────────────── Broadcast (Reklama) ────────────────

@router.callback_query(F.data == "adm:broadcast", filter_admin)
async def on_admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Start broadcast flow."""
    await callback.message.edit_text(
        "📢 <b>Reklama xabarini yuboring.</b>\n\n"
        "Xabar barcha foydalanuvchilar va guruhlarga tarqatiladi (rasm/video/matn bo'lishi mumkin).",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_broadcast_message)
    await callback.answer()


@router.message(AdminStates.waiting_broadcast_message, filter_admin)
async def on_broadcast_message(message: Message, state: FSMContext):
    """Receive broadcast message and send to users/groups (with throttling)."""
    groups = db.get_all_groups()

    await state.clear()

    # Exclude the group where orders are received
    order_group = int(ORDERS_GROUP_ID) if ORDERS_GROUP_ID and ORDERS_GROUP_ID.replace('-', '').isdigit() else None
    target_chats = [g["group_id"] for g in groups if g["group_id"] != order_group]
    total = len(target_chats)

    if total == 0:
        await message.answer("Oluvchi guruhlar mavjud emas.", reply_markup=admin_back_keyboard())
        return

    status_msg = await message.answer(f"⏳ Tarqatma boshlandi... (Jami guruhlar: {total} ta)")

    success = 0
    fail = 0

    for chat_id in target_chats:
        try:
            await message.copy_to(chat_id=chat_id)
            success += 1
        except Exception as e:
            logger.error(f"Broadcast failed for {chat_id}: {e}")
            fail += 1
            # If kicked or chat not found, you could auto-remove from db here if needed
            if "group" in str(e).lower() or "chat not found" in str(e).lower():
                db.remove_group(chat_id)
        
        # Anti-spam delay
        await asyncio.sleep(BROADCAST_DELAY)

    text = (
        "✅ <b>Tarqatma yakunlandi!</b>\n\n"
        f"Jami yuborildi: {success} ta guruhga\n"
        f"Xatoliklar (bloklaganlar/o'chganlar): {fail} ta"
    )

    await status_msg.edit_text(text, reply_markup=admin_back_keyboard(), parse_mode="HTML")


# ──────────────── Auto-Broadcast Campaigns ────────────────

@router.callback_query(F.data == "adm:ab_list", filter_admin)
async def on_ab_list(callback: CallbackQuery, state: FSMContext):
    """Show list of all auto-broadcast campaigns."""
    await state.clear()
    campaigns = db.get_campaigns()
    await callback.message.edit_text(
        "⚙️ <b>Avto-Reklamalar Ro'yxati</b>\n\n"
        "Shu yerdan bir nechta mustaqil reklamalarni taymer bilan sozlashingiz mumkin.",
        reply_markup=admin_campaigns_keyboard(campaigns),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "adm_camp_add", filter_admin)
async def on_camp_add_start(callback: CallbackQuery, state: FSMContext):
    """Start wizard to create a new campaign."""
    await state.clear()
    await callback.message.edit_text(
        "📝 <b>Yangi Avto-Reklama qo'shish (1-qadam)</b>\n\n"
        "Iltimos, ushbu kampaniya uchun reklama rasm, video yoki oddiy matnini yuboring:",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_new_cp_msg)
    await callback.answer()

@router.message(AdminStates.waiting_new_cp_msg, filter_admin)
async def on_new_camp_msg_received(message: Message, state: FSMContext):
    await state.update_data(
        new_cp_msg_id=message.message_id,
        new_cp_from_chat=message.chat.id
    )
    await message.answer(
        "⏱ <b>Yangi Avto-Reklama (2-qadam)</b>\n\n"
        "Xabar qabul qilindi! Endi bu taymer har qancha vaqtda qaytarilishini raqamda yozing:\n"
        "(Masalan: <code>60</code> bu 1 soatda degani, <code>120</code> bu 2 soat)",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_new_cp_interval)

@router.message(AdminStates.waiting_new_cp_interval, filter_admin)
async def on_new_camp_interval_received(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("⚠️ Iltimos faqat raqam kiriting (masalan: 60)")
        return
        
    minutes = int(message.text)
    if minutes < 1:
        await message.answer("⚠️ Interval juda qisqa.")
        return
        
    data = await state.get_data()
    msg_id = data.get("new_cp_msg_id")
    from_chat = data.get("new_cp_from_chat")
    
    # Create the actual campaign
    camp = db.add_campaign(message_id=msg_id, from_chat_id=from_chat, interval_minutes=minutes)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Reklama #{camp['id']} yaratildi va YOQILDI!</b>\n\n"
        f"Har {minutes} daqiqada doimiy aylanib turadi. Uni boshqarish uchun quyidagi menyudan foydalanasiz:",
        reply_markup=admin_single_campaign_keyboard(camp),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("adm_camp:"), filter_admin)
async def on_camp_select(callback: CallbackQuery):
    """Select a specific campaign to edit."""
    camp_id = int(callback.data.split(":")[1])
    camps = db.get_campaigns()
    camp = next((c for c in camps if c["id"] == camp_id), None)
    if not camp:
        await callback.answer("Topilmadi", show_alert=True)
        return
    await callback.message.edit_text(
        f"⚙️ <b>Reklama #{camp['id']}</b>\n\nQuyidagi tugmalar orqali sozlang.",
        reply_markup=admin_single_campaign_keyboard(camp),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("adm_cp_del:"), filter_admin)
async def on_camp_delete(callback: CallbackQuery):
    """Delete a campaign."""
    camp_id = int(callback.data.split(":")[1])
    db.delete_campaign(camp_id)
    await callback.answer("🗑 O'chirildi", show_alert=True)
    campaigns = db.get_campaigns()
    await callback.message.edit_text(
        "⚙️ <b>Avto-Reklamalar Ro'yxati</b>\n\n"
        "Shu yerdan bir nechta mustaqil reklamalarni taymer bilan sozlashingiz mumkin.",
        reply_markup=admin_campaigns_keyboard(campaigns),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("adm_cp_tg:"), filter_admin)
async def on_camp_toggle(callback: CallbackQuery):
    """Toggle a campaign."""
    camp_id = int(callback.data.split(":")[1])
    camps = db.get_campaigns()
    camp = next((c for c in camps if c["id"] == camp_id), None)
    if not camp:
        return
        
    if not camp.get("is_active") and not camp.get("message_id"):
        await callback.answer("❌ Avval reklama xabarini o'rnating!", show_alert=True)
        return
        
    new_status = not camp.get("is_active", False)
    db.update_campaign(camp_id, is_active=new_status)
    camp["is_active"] = new_status
    
    text = "yoqildi 🟢" if new_status else "to'xtatildi 🔴"
    await callback.answer(f"Reklama {text}")
    
    await callback.message.edit_reply_markup(
        reply_markup=admin_single_campaign_keyboard(camp)
    )

@router.callback_query(F.data.startswith("adm_cp_msg:"), filter_admin)
async def on_camp_msg_start(callback: CallbackQuery, state: FSMContext):
    """Ask for the auto-broadcast message."""
    camp_id = int(callback.data.split(":")[1])
    await state.update_data(camp_id=camp_id)
    await callback.message.edit_text(
        "📝 <b>Ushbu kampaniya uchun yangi xabarni yuboring.</b>\n\n"
        "Bu xabar rasm, video yoki oddiy matn bo'lishi mumkin.",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_cp_message)
    await callback.answer()

@router.message(AdminStates.waiting_cp_message, filter_admin)
async def on_camp_message_received(message: Message, state: FSMContext):
    data = await state.get_data()
    camp_id = data.get("camp_id")
    
    db.update_campaign(
        camp_id,
        message_id=message.message_id,
        from_chat_id=message.chat.id
    )
    await state.clear()
    
    camps = db.get_campaigns()
    camp = next((c for c in camps if c["id"] == camp_id), None)
    
    await message.answer(
        "✅ <b>Avto-reklama xabari muvaffaqiyatli saqlandi!</b>",
        reply_markup=admin_single_campaign_keyboard(camp),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("adm_cp_time:"), filter_admin)
async def on_camp_time_start(callback: CallbackQuery, state: FSMContext):
    camp_id = int(callback.data.split(":")[1])
    await state.update_data(camp_id=camp_id)
    await callback.message.edit_text(
        "⏱ <b>Reklama oralig'i (interval)</b>\n\n"
        "Faqat raqam kiriting (masalan: <code>60</code> bu 1 soat degani)",
        reply_markup=admin_back_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_cp_interval)
    await callback.answer()

@router.message(AdminStates.waiting_cp_interval, filter_admin)
async def on_camp_interval_received(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("⚠️ Faqat raqam kiriting (masalan: 60)")
        return
        
    minutes = int(message.text)
    if minutes < 1:
        await message.answer("⚠️ Interval juda qisqa.")
        return
        
    data = await state.get_data()
    camp_id = data.get("camp_id")
    
    db.update_campaign(camp_id, interval_minutes=minutes)
    await state.clear()
    
    camps = db.get_campaigns()
    camp = next((c for c in camps if c["id"] == camp_id), None)
    
    await message.answer(
        f"✅ Taymer o'zgartirildi: har <b>{minutes}</b> daqiqada.",
        reply_markup=admin_single_campaign_keyboard(camp),
        parse_mode="HTML"
    )
