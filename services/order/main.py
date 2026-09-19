from contextlib import asynccontextmanager
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from common.infra import create_producer, event, wait_for_postgres


class OrderCreate(BaseModel):
    user_id: UUID
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)
    total: Decimal = Field(gt=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await wait_for_postgres()
    await app.state.db.execute(
        """CREATE TABLE IF NOT EXISTS orders (
        id UUID PRIMARY KEY, user_id UUID NOT NULL, item_id INT NOT NULL,
        quantity INT NOT NULL, total NUMERIC(10,2) NOT NULL, status TEXT NOT NULL)"""
    )
    app.state.producer = await create_producer()
    yield
    await app.state.producer.stop()
    await app.state.db.close()


app = FastAPI(title="UniEats Order Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"service": "order", "status": "ok"}


@app.post("/orders", status_code=202)
async def create_order(body: OrderCreate):
    order_id = uuid4()
    await app.state.db.execute(
        "INSERT INTO orders VALUES($1,$2,$3,$4,$5,$6)",
        order_id, body.user_id, body.item_id, body.quantity, body.total, "CREATED",
    )
    payload = {
        "order_id": str(order_id), "user_id": str(body.user_id),
        "item_id": body.item_id, "quantity": body.quantity, "total": str(body.total),
    }
    # HTTP уже может завершиться: дальнейшая цепочка идет асинхронно через Kafka.
    await app.state.producer.send_and_wait("order.created", event("OrderCreated", payload))
    return {"order_id": str(order_id), "status": "CREATED"}