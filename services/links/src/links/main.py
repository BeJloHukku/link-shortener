from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Request,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from links.api.routes import router
from links.infrastructure.broker.rabbitmq import (
    NullBroker,
    RabbitMQBroker,
)
from links.infrastructure.broker.rabbitmq_settings import connect_rabbitmq
from links.infrastructure.db.db import engine
from links.infrastructure.db.models import Base
from links.settings import (
    CORS_ORIGINS,
    RABBITMQ_URL,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    rabbit = await connect_rabbitmq(url=RABBITMQ_URL)
    if rabbit is None:
        app.state.broker = NullBroker()
    else:
        _, exchange = rabbit
        app.state.broker = RabbitMQBroker(exchange)
    try:
        yield
    finally:
        if rabbit is not None:
            connection, _ = rabbit
            await connection.close()


app = FastAPI(lifespan=lifespan)

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Неверный формат ввода!"},
    )


app.include_router(router)
