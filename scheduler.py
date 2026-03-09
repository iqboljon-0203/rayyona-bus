"""
Simple async scheduler to handle auto-broadcasting messages at set intervals.
"""
import asyncio
import logging
from aiogram import Bot

import database as db
from config import BROADCAST_DELAY, ORDERS_GROUP_ID

logger = logging.getLogger(__name__)


async def auto_broadcast_worker(bot: Bot):
    """Background task that runs periodically to check if auto-broadcast should trigger."""
    import time
    # Give Bot API a moment to connect
    await asyncio.sleep(5)
    
    while True:
        try:
            campaigns = db.get_campaigns()
            current_time = time.time()

            for c in campaigns:
                if not c.get("is_active", False):
                    continue
                    
                interval_minutes = c.get("interval_minutes", 60)
                msg_id = c.get("message_id")
                from_chat_id = c.get("from_chat_id")
                last_run = c.get("last_run", 0)

                seconds_passed = current_time - last_run
                if seconds_passed >= (interval_minutes * 60) and msg_id and from_chat_id:
                    logger.info(f"Avto-reklama #{c['id']} intervali yetib keldi. Tarqatish boshlanmoqda...")
                    
                    groups = db.get_all_groups()
                    order_group = int(ORDERS_GROUP_ID) if ORDERS_GROUP_ID and ORDERS_GROUP_ID.replace('-', '').isdigit() else None
                    target_chats = [g["group_id"] for g in groups if g["group_id"] != order_group]
                    
                    success = 0
                    fail = 0
                    
                    for chat_id in target_chats:
                        try:
                            await bot.copy_message(
                                chat_id=chat_id,
                                from_chat_id=from_chat_id,
                                message_id=msg_id
                            )
                            success += 1
                        except Exception as e:
                            logger.error(f"Auto-broadcast failed for {chat_id}: {e}")
                            fail += 1
                            if "group" in str(e).lower() or "chat not found" in str(e).lower():
                                db.remove_group(chat_id)
                                
                        # Anti-spam delay
                        await asyncio.sleep(BROADCAST_DELAY)
                        
                    logger.info(f"Avto-reklama #{c['id']} yakunlandi: Muvaffaqiyatli: {success}, Xatolar: {fail}")
                    # Update last run time in DB
                    db.update_campaign(c["id"], last_run=time.time())

            # Wait a minute before checking again
            await asyncio.sleep(60)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in auto_broadcast_worker: {e}")
            await asyncio.sleep(60)
