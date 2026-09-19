import asyncio
from contextlib import asynccontextmanager, suppress
from uuid import UUID

from fastapi import FastAPI

from common.infra import consume_forever, create_producer, event, wait_for_postgres


async def handle_order(topic: str, message: dict) -> None:
    payload = message["payload"]
    order_id = UUID(payload["order_id"])
    # ON CONFLICT делает consumer идемпотентным при повторной доставке сообщения.
    await app.state.db.execute(
        """INSERT INTO kitchen_orders(order_id, status) VALUES($1, 'ACCEPTED')
        ON CONFLICT(order_id) DO UPDATE SET status='ACCEPTED'""", order_id,
    )
    await app.state.producer.send_and_wait(
        "kitchen.order.accepted",
        event("KitchenOrderAccepted", {"order_id": str(order_id), "user_id": payload["user_id"]}),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await wait_for_postgres()
    await app.state.db.execute(
        "CREATE TABLE IF NOT EXISTS kitchen_orders (order_id UUID PRIMARY KEY, status TEXT NOT NULL)"
    )
    app.state.producer = await create_producer()
    task = asyncio.create_task(consume_forever(["order.created"], "kitchen-service", handle_order))
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    await app.state.producer.stop()
    await app.state.db.close()


app = FastAPI(title="UniEats Kitchen Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"service": "kitchen", "status": "ok"}


@app.get("/orders")
async def orders():
    rows = await app.state.db.fetch("SELECT order_id::text, status FROM kitchen_orders")
    return [dict(row) for row in rows]