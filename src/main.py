from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.errors import register_exception_handlers
from src.routers.agentic_ask import router as agentic_ask_router
from src.routers.ask import router as ask_router
from src.routers.chunk_search import router as chunk_search_router
from src.routers.feedback import router as feedback_router
from src.routers.health import router as health_router
from src.routers.hybrid_search import router as hybrid_search_router
from src.routers.papers import router as papers_router
from src.routers.search import router as search_router
from src.services.cache.factory import make_cache_client
from src.services.embeddings.factory import make_embeddings_client
from src.services.langfuse.factory import make_tracer_service
from src.services.ollama.factory import make_ollama_client
from src.services.opensearch.factory import make_opensearch_client
from src.services.telegram.bot import TelegramBotService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.opensearch_client = make_opensearch_client()
    app.state.ollama_client = make_ollama_client()
    app.state.cache_client = make_cache_client()
    app.state.embeddings_client = make_embeddings_client()
    app.state.tracer_service = make_tracer_service()
    app.state.telegram_bot = None

    telegram_cfg = settings.telegram
    if telegram_cfg.enabled and telegram_cfg.bot_token:
        bot = TelegramBotService(
            bot_token=telegram_cfg.bot_token,
            api_base_url=telegram_cfg.api_base_url,
            poll_interval_seconds=telegram_cfg.poll_interval_seconds,
        )
        await bot.start()
        app.state.telegram_bot = bot

    try:
        yield
    finally:
        bot = getattr(app.state, "telegram_bot", None)
        if bot:
            await bot.stop()
        tracer = getattr(app.state, "tracer_service", None)
        if tracer:
            tracer.shutdown()


app = FastAPI(title=settings.app.name, lifespan=lifespan)
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(papers_router)
app.include_router(search_router)
app.include_router(chunk_search_router)
app.include_router(hybrid_search_router)
app.include_router(ask_router)
app.include_router(agentic_ask_router)
app.include_router(feedback_router)


@app.get("/")
def root() -> dict:
    return {"message": "Part 1 infrastructure is up"}
