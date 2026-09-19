import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from redis.asyncio import Redis

from common.infra import wait_for_postgres


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await wait_for_postgres()
    app.state.cache = Redis.from_url(os.getenv("REDIS_URL", "redis://valkey:6379"), decode_responses=True)
    await app.state.db.execute(
        """CREATE TABLE IF NOT EXISTS catalog_items (
        id SERIAL PRIMARY KEY, name TEXT NOT NULL, price NUMERIC(10,2) NOT NULL, available BOOLEAN NOT NULL)"""
    )
    count = await app.state.db.fetchval("SELECT COUNT(*) FROM catalog_items")
    if count == 0:
        await app.state.db.executemany(
            "INSERT INTO catalog_items(name, price, available) VALUES($1, $2, true)",
            [("Сэндвич", 220), ("Салат", 180), ("Кофе", 120)],
        )
    yield
    await app.state.cache.aclose()
    await app.state.db.close()


app = FastAPI(title="UniEats Catalog Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"service": "catalog", "status": "ok"}


@app.get("/items")
async def items(response: Response):
    # Cache-aside: сначала читаем быстрый кэш, при промахе — БД и наполняем кэш.
    cached = await app.state.cache.get("catalog:items")
    if cached:
        response.headers["X-Cache"] = "HIT"
        return json.loads(cached)
    rows = await app.state.db.fetch(
        "SELECT id, name, price::float, available FROM catalog_items ORDER BY id"
    )
    result = [dict(row) for row in rows]
    await app.state.cache.set("catalog:items", json.dumps(result), ex=60)
    response.headers["X-Cache"] = "MISS"
    return result