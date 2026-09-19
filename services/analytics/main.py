import asyncio
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from pymongo import AsyncMongoClient

from common.infra import consume_forever


async def archive_event(topic: str, message: dict) -> None:
    # MongoDB хранит разные типы событий без общей табличной схемы — удобно для истории.
    await app.state.collection.update_one(
        {"event_id": message["event_id"]},
        {"$setOnInsert": {**message, "topic": topic}},
        upsert=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo = AsyncMongoClient(os.getenv("MONGO_URL", "mongodb://uni:uni_dev_password@mongo:27017"))
    app.state.collection = app.state.mongo.unieats.event_archive
    task = asyncio.create_task(consume_forever(
        ["order.created", "kitchen.order.accepted"], "analytics-service", archive_event
    ))
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    await app.state.mongo.close()


app = FastAPI(title="UniEats Analytics Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"service": "analytics", "status": "ok"}


@app.get("/stats")
async def stats():
    pipeline = [{"$group": {"_id": "$event_type", "count": {"$sum": 1}}}]
    cursor = await app.state.collection.aggregate(pipeline)
    rows = await cursor.to_list(length=100)
    return {row["_id"]: row["count"] for row in rows}