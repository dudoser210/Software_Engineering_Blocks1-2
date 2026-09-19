from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from common.infra import wait_for_postgres


class UserCreate(BaseModel):
    name: str
    email: EmailStr


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await wait_for_postgres()
    await app.state.db.execute(
        """CREATE TABLE IF NOT EXISTS identity_users (
        id UUID PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL)"""
    )
    yield
    await app.state.db.close()


app = FastAPI(title="UniEats Identity Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"service": "identity", "status": "ok"}


@app.post("/users", status_code=201)
async def create_user(body: UserCreate):
    user_id = uuid4()
    try:
        await app.state.db.execute(
            "INSERT INTO identity_users(id, name, email) VALUES($1, $2, $3)",
            user_id, body.name, body.email,
        )
    except Exception as exc:
        raise HTTPException(409, "Пользователь с таким email уже существует") from exc
    return {"id": str(user_id), **body.model_dump()}