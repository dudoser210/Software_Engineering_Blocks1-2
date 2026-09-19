import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import uuid4

import asyncpg
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


def env(name: str, default: str) -> str:
    """Берем настройку из Docker environment, а default помогает локальной разработке."""
    return os.getenv(name, default)


async def wait_for_postgres() -> asyncpg.Pool:
    """Инфраструктура стартует не мгновенно, поэтому сервис терпеливо повторяет подключение."""
    dsn = env("POSTGRES_DSN", "postgresql://uni:uni_dev_password@postgres:5432/unieats")
    for attempt in range(30):
        try:
            return await asyncpg.create_pool(dsn, min_size=1, max_size=5)
        except Exception:
            if attempt == 29:
                raise
            await asyncio.sleep(2)
    raise RuntimeError("PostgreSQL is unavailable")


async def create_producer() -> AIOKafkaProducer:
    """Producer сериализует словарь в JSON. Kafka хранит событие независимо от consumers."""
    producer = AIOKafkaProducer(
        bootstrap_servers=env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )
    for attempt in range(30):
        try:
            await producer.start()
            return producer
        except Exception:
            if attempt == 29:
                raise
            await asyncio.sleep(2)
    raise RuntimeError("Kafka is unavailable")


def event(event_type: str, payload: dict) -> dict:
    """Единый envelope упрощает трассировку и версионирование сообщений."""
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "event_version": 1,
        "occurred_at": datetime.now(UTC).isoformat(),
        "payload": payload,
    }


async def consume_forever(
    topics: list[str], group_id: str, handler: Callable[[str, dict], Awaitable[None]]
) -> None:
    """Consumer group гарантирует: одно событие обрабатывает один экземпляр сервиса."""
    consumer = AIOKafkaConsumer(
        *topics,
        bootstrap_servers=env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
    )
    for attempt in range(30):
        try:
            await consumer.start()
            break
        except Exception:
            if attempt == 29:
                raise
            await asyncio.sleep(2)
    try:
        async for message in consumer:
            await handler(message.topic, message.value)
            # Commit выполняется после успешного handler: это модель at-least-once.
            await consumer.commit()
    finally:
        await consumer.stop()