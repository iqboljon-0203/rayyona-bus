"""
Group lifecycle handlers for the bus booking bot.
Handles: bot added/removed from groups, auto-tracking in database.
"""

import logging
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, ADMINISTRATOR

import database as db

logger = logging.getLogger(__name__)
router = Router()


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=IS_NOT_MEMBER >> (IS_MEMBER | ADMINISTRATOR)
    )
)
async def on_bot_added_to_group(event: ChatMemberUpdated):
    """Bot was added to a group — save group info to database."""
    chat = event.chat

    if chat.type in ("group", "supergroup"):
        db.add_group(
            group_id=chat.id,
            title=chat.title or "Nomsiz guruh"
        )
        logger.info(f"Bot added to group: {chat.title} ({chat.id})")

        pass


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(IS_MEMBER | ADMINISTRATOR) >> IS_NOT_MEMBER
    )
)
async def on_bot_removed_from_group(event: ChatMemberUpdated):
    """Bot was removed from a group — remove from database."""
    chat = event.chat

    if chat.type in ("group", "supergroup"):
        db.remove_group(chat.id)
        logger.info(f"Bot removed from group: {chat.title} ({chat.id})")
