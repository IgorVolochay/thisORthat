import os
import json
import asyncio
import logging
from typing import Callable, Awaitable

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from dotenv import load_dotenv

from schemas.base_schemas import Card


logger = logging.getLogger(__name__)


class RabbitWorker:
    def __init__(self):
        load_dotenv()
        self.url = (
            f"amqp://{os.getenv('RABBIT_USER')}:{os.getenv('RABBIT_PASS')}"
            f"@{os.getenv('RABBIT_HOST')}:{os.getenv('RABBIT_PORT')}"
        )

    async def send_to_moderation(self, card: Card) -> None:
        """Отправляет карточку в очередь модерации."""
        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("moderation", durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=card.model_dump_json().encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key="moderation",
            )
            logger.info("Card %s sent to moderation queue", card.card_id)

    async def consume_moderation(
        self,
        callback: Callable[[Card], Awaitable[None]],
    ) -> None:
        """Бесконечно слушает очередь модерации и вызывает callback для каждой карточки."""
        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue("moderation", durable=True)

            logger.info("Started consuming moderation queue...")

            async def on_message(message: AbstractIncomingMessage) -> None:
                async with message.process():
                    try:
                        card_data = json.loads(message.body.decode())
                        card = Card.model_validate(card_data)
                        await callback(card)
                    except Exception as exc:
                        logger.error("Error processing moderation message: %s", exc)

            await queue.consume(on_message)

            # Держим consumer живым, но позволяем отмену (Ctrl+C)
            stop_event = asyncio.Event()
            try:
                await stop_event.wait()
            except asyncio.CancelledError:
                logger.info("Moderation consumer shutting down...")
                raise