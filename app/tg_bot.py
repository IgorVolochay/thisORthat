"""
Telegram-бот модерации карточек.

Слушает очередь RabbitMQ «moderation» и отправляет карточки
в чат администратору с inline-кнопками «Принять ✅» / «Отклонить ❌».

При нажатии кнопки бот вызывает защищённые эндпоинты
/card_accept или /card_reject с секретным заголовком.
"""

import os
import json
import asyncio
import logging
from datetime import datetime

import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from schemas.base_schemas import Card
from rabbit_worker import RabbitWorker


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Конфигурация ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("TG_ADMIN_CHAT_ID", "0"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
MODERATION_SECRET = os.getenv("MODERATION_SECRET", "change-me-in-production")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
rabbit = RabbitWorker()


# ── Отправка карточки администратору ──────────────────────────
async def _get_author_username(author_id: int) -> str:
    """Запрашивает username автора через API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/get_user", params={"user_id": author_id}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    username = data.get("result", {}).get("username", "")
                    if username:
                        return f"@{username}"
    except Exception as exc:
        logger.warning("Failed to fetch username for %s: %s", author_id, exc)
    return str(author_id)


def _format_date(iso_date: str) -> str:
    """Преобразует ISO-дату в формат ДД.ММ.ГГГГ ЧЧ:ММ:СС."""
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    except (ValueError, TypeError):
        return iso_date


async def send_card_to_admin(card: Card) -> None:
    """Формирует сообщение и inline-клавиатуру для карточки."""
    author_display = await _get_author_username(card.author_id)
    date_display = _format_date(card.creation_date)

    text = (
        f"🆕 <b>Новая карточка #{card.card_id}</b>\n\n"
        f"🅰️ {card.choice_A}\n"
        f"🅱️ {card.choice_B}\n\n"
        f"👤 Автор: {author_display}\n"
        f"📅 Создана: {date_display}"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Принять ✅",
                    callback_data=f"accept:{card.card_id}",
                ),
                InlineKeyboardButton(
                    text="Отклонить ❌",
                    callback_data=f"reject:{card.card_id}",
                ),
            ]
        ]
    )
    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    logger.info("Sent card %s to admin chat", card.card_id)


# ── Вызов защищённых эндпоинтов API ──────────────────────────
async def call_moderation_api(action: str, card_id: int) -> dict:
    """
    Вызывает /card_accept или /card_reject с секретным заголовком.
    action: 'accept' | 'reject'
    """
    endpoint = f"{API_BASE_URL}/card_{action}"
    headers = {"X-Moderation-Secret": MODERATION_SECRET}
    params = {"card_id": card_id}

    async with aiohttp.ClientSession() as session:
        async with session.patch(endpoint, headers=headers, params=params) as resp:
            data = await resp.json()
            return data


# ── Обработчики callback-кнопок ───────────────────────────────
@dp.callback_query(F.data.startswith("accept:"))
async def on_accept(callback: CallbackQuery) -> None:
    card_id = int(callback.data.split(":")[1])
    result = await call_moderation_api("accept", card_id)

    if result.get("error"):
        await callback.answer(f"Ошибка: {result['result']}", show_alert=True)
        return

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>ПРИНЯТА</b>",
        parse_mode="HTML",
    )
    await callback.answer("Карточка принята!")
    logger.info("Card %s accepted by admin", card_id)


@dp.callback_query(F.data.startswith("reject:"))
async def on_reject(callback: CallbackQuery) -> None:
    card_id = int(callback.data.split(":")[1])
    result = await call_moderation_api("reject", card_id)

    if result.get("error"):
        await callback.answer(f"Ошибка: {result['result']}", show_alert=True)
        return

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <b>ОТКЛОНЕНА</b>",
        parse_mode="HTML",
    )
    await callback.answer("Карточка отклонена!")
    logger.info("Card %s rejected by admin", card_id)

# ── Lifecycle-хуки aiogram ────────────────────────────────────
_rabbit_task: asyncio.Task | None = None


@dp.startup()
async def on_startup() -> None:
    global _rabbit_task
    _rabbit_task = asyncio.create_task(
        rabbit.consume_moderation(send_card_to_admin)
    )
    logger.info("Moderation bot started, RabbitMQ consumer running")


@dp.shutdown()
async def on_shutdown() -> None:
    if _rabbit_task:
        _rabbit_task.cancel()
        try:
            await _rabbit_task
        except asyncio.CancelledError:
            pass
    logger.info("Moderation bot stopped")


if __name__ == "__main__":
    dp.run_polling(bot)
