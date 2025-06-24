from contextlib import asynccontextmanager

from api.v1 import chat as chat_router
from config import settings
from core.logging import get_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

origins = [
    settings.FRONTEND_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router.router, prefix="/api/v1", tags=["chat"])
