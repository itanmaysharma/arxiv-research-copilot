import asyncio

from src.services.telegram.bot import TelegramBotService


def test_handle_help_command_sends_usage(monkeypatch):
    bot = TelegramBotService(bot_token="x", api_base_url="http://localhost:8000")
    sent = []

    async def fake_send(chat_id: int, text: str):
        sent.append((chat_id, text))

    monkeypatch.setattr(bot, "_send_message", fake_send)

    asyncio.run(bot.handle_message(chat_id=1001, text="/start"))

    assert len(sent) == 1
    assert "Use /ask" in sent[0][1]


def test_handle_ask_command_calls_ask_endpoint(monkeypatch):
    bot = TelegramBotService(bot_token="x", api_base_url="http://localhost:8000")
    sent = []
    calls = []

    async def fake_query(path: str, question: str):
        calls.append((path, question))
        return "answer-from-ask"

    async def fake_send(chat_id: int, text: str):
        sent.append((chat_id, text))

    monkeypatch.setattr(bot, "_query_api", fake_query)
    monkeypatch.setattr(bot, "_send_message", fake_send)

    asyncio.run(bot.handle_message(chat_id=1001, text="/ask what is rag?"))

    assert calls == [("/api/v1/ask", "what is rag?")]
    assert sent == [(1001, "answer-from-ask")]


def test_handle_agentic_command_calls_agentic_endpoint(monkeypatch):
    bot = TelegramBotService(bot_token="x", api_base_url="http://localhost:8000")
    sent = []
    calls = []

    async def fake_query(path: str, question: str):
        calls.append((path, question))
        return "answer-from-agentic"

    async def fake_send(chat_id: int, text: str):
        sent.append((chat_id, text))

    monkeypatch.setattr(bot, "_query_api", fake_query)
    monkeypatch.setattr(bot, "_send_message", fake_send)

    asyncio.run(bot.handle_message(chat_id=1001, text="/agentic explain ponte"))

    assert calls == [("/api/v1/agentic-ask", "explain ponte")]
    assert sent == [(1001, "answer-from-agentic")]


def test_handle_unknown_command(monkeypatch):
    bot = TelegramBotService(bot_token="x", api_base_url="http://localhost:8000")
    sent = []

    async def fake_send(chat_id: int, text: str):
        sent.append((chat_id, text))

    monkeypatch.setattr(bot, "_send_message", fake_send)

    asyncio.run(bot.handle_message(chat_id=1001, text="hello bot"))

    assert len(sent) == 1
    assert "Unknown command" in sent[0][1]
