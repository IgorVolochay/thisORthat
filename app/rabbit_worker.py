import os
import json
import asyncio
from typing import Callable, Awaitable

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from dotenv import load_dotenv

from schemas.base_schemas import Card
from logger import logger


class RabbitWorker:
    """Handles RabbitMQ connections and message publishing/consuming for moderation."""
    def __init__(self):
        """Initializes the RabbitWorker with connection credentials from environment variables."""
        load_dotenv()
        self.url = (
            f"amqp://{os.getenv('RABBIT_USER')}:{os.getenv('RABBIT_PASS')}"
            f"@{os.getenv('RABBIT_HOST')}:{os.getenv('RABBIT_PORT')}"
        )
        logger.info("RabbitWorker connection established.")

    async def send_to_moderation(self, card: Card) -> None:
        """Publishes a card to the 'moderation' RabbitMQ queue."""
        logger.debug("Preparing to send card {} to moderation queue...", card.card_id)
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
            logger.debug("Card {} successfully published to moderation queue", card.card_id)
            logger.info("Card {} sent to moderation queue", card.card_id)

    async def consume_moderation(
        self,
        callback: Callable[[Card], Awaitable[None]],
    ) -> None:
        """
        Consumes messages from the 'moderation' queue and processes them using the provided callback.
        
        Args:
            callback: An async function that takes a Card object and processes it.
        """
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
                        logger.error("Error processing moderation message: {}", exc)

            await queue.consume(on_message)

            # Keep consumer alive while allowing cancellation (Ctrl+C)
            stop_event = asyncio.Event()
            try:
                await stop_event.wait()
            except asyncio.CancelledError:
                logger.info("Moderation consumer shutting down...")
                raise