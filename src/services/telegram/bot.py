import asyncio
from typing import Any

import httpx


class TelegramBotService:
    def __init__(
        self,
        bot_token: str,
        api_base_url: str,
        poll_interval_seconds: float = 2.0,
    ) -> None:
        self.bot_token = bot_token.strip()
        self.api_base_url = api_base_url.rstrip("/")
        self.poll_interval_seconds = max(0.5, float(poll_interval_seconds))
        self._task: asyncio.Task | None = None
        self._running = False
        self._offset: int | None = None

    async def start(self) -> None:
        if not self.bot_token or self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        print("[telegram] bot started")

    async def stop(self) -> None:
        self._running = False
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
        print("[telegram] bot stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                updates = await self._get_updates(timeout_seconds=20)
                for update in updates:
                    await self._handle_update(update)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"[telegram] loop error={exc}")
                await asyncio.sleep(self.poll_interval_seconds)

    async def _get_updates(self, timeout_seconds: int = 20) -> list[dict]:
        payload: dict[str, Any] = {"timeout": timeout_seconds}
        if self._offset is not None:
            payload["offset"] = self._offset
        response = await self._telegram_request("getUpdates", payload)
        updates = response.get("result", [])
        if updates:
            self._offset = int(updates[-1]["update_id"]) + 1
        return updates

    async def _handle_update(self, update: dict) -> None:
        message = update.get("message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        text = (message.get("text") or "").strip()
        if not chat_id or not text:
            return
        await self.handle_message(chat_id=int(chat_id), text=text)

    async def handle_message(self, chat_id: int, text: str) -> None:
        lowered = text.lower()
        if lowered in {"/start", "/help"}:
            await self._send_message(
                chat_id,
                "Use /ask <question> or /agentic <question> to query the research assistant.",
            )
            return

        if text.startswith("/ask "):
            question = text[len("/ask ") :].strip()
            if not question:
                await self._send_message(chat_id, "Please provide a question after /ask.")
                return
            answer = await self._query_api("/api/v1/ask", question)
            await self._send_message(chat_id, answer)
            return

        if text.startswith("/agentic "):
            question = text[len("/agentic ") :].strip()
            if not question:
                await self._send_message(chat_id, "Please provide a question after /agentic.")
                return
            answer = await self._query_api("/api/v1/agentic-ask", question)
            await self._send_message(chat_id, answer)
            return

        await self._send_message(
            chat_id,
            "Unknown command. Use /ask <question> or /agentic <question>.",
        )

    async def _query_api(self, path: str, question: str) -> str:
        try:
            payload = {"question": question, "top_k": 3}
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.api_base_url}{path}", json=payload)
                resp.raise_for_status()
            data = resp.json()
            answer = str(data.get("answer", "No answer returned.")).strip()
            if len(answer) > 3500:
                answer = answer[:3500] + "..."
            return answer
        except Exception as exc:
            return f"Request failed: {exc}"

    async def _send_message(self, chat_id: int, text: str) -> None:
        await self._telegram_request(
            "sendMessage",
            {"chat_id": chat_id, "text": text},
        )

    async def _telegram_request(self, method: str, payload: dict) -> dict:
        url = f"https://api.telegram.org/bot{self.bot_token}/{method}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        data = resp.json()
        if not data.get("ok", False):
            raise RuntimeError(f"telegram method failed: {method}")
        return data
