import asyncio
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from pymongo import AsyncMongoClient

from common.infra import consume_forever


async def handle_event(topic: str, message: dict) -> None:
    # В учебной версии "отправка" — запись уведомления. Здесь легко добавить email/SMS adapter.
    await app.state.collection.insert_one({
        "topic": topic,
        "event_id": message["event_id"],
        "user_id": message["payload"].get("user_id"),
        "text": f"Получено событие {message['event_type']}",
        "occurred_at": message["occurred_at"],
    })


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo = AsyncMongoClient(os.getenv("MONGO_URL", "mongodb://uni:uni_dev_password@mongo:27017"))
    app.state.collection = app.state.mongo.unieats.notifications
    task = asyncio.create_task(consume_forever(
        ["order.created", "kitchen.order.accepted"], "notification-service", handle_event
    ))
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    await app.state.mongo.close()


app = FastAPI(title="UniEats Notification Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"service": "notification", "status": "ok"}


@app.get("/notifications")
async def notifications():
    cursor = app.state.collection.find({}, {"_id": 0}).sort("occurred_at", -1).limit(20)
    return await cursor.to_list(length=20)