import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from src.config import settings

try:
    from langfuse import Langfuse
except Exception:  # pragma: no cover - optional import safety
    Langfuse = None  # type: ignore[assignment]


def _safe_call(obj: Any, method: str, **kwargs: Any) -> Any:
    fn = getattr(obj, method, None)
    if not callable(fn):
        return None
    try:
        return fn(**kwargs)
    except Exception:
        return None


@dataclass
class TraceSession:
    trace_name: str
    trace_id: str
    enabled: bool
    trace_obj: Any | None = None
    started_at: float = field(default_factory=time.perf_counter)

    @contextmanager
    def span(self, span_name: str, **metadata: Any):
        span_started = time.perf_counter()
        status = "ok"
        error: str | None = None
        span_obj = None

        if self.enabled and self.trace_obj is not None:
            span_obj = _safe_call(self.trace_obj, "span", name=span_name, metadata=metadata or None)

        try:
            yield
        except Exception as exc:
            status = "error"
            error = str(exc)
            raise
        finally:
            elapsed_ms = int((time.perf_counter() - span_started) * 1000)
            if self.enabled:
                payload: dict[str, Any] = {
                    "trace_id": self.trace_id,
                    "trace": self.trace_name,
                    "span": span_name,
                    "status": status,
                    "elapsed_ms": elapsed_ms,
                }
                if metadata:
                    payload["meta"] = metadata
                if error:
                    payload["error"] = error
                print(f"[trace] {json.dumps(payload, sort_keys=True)}")

            if span_obj is not None:
                _safe_call(
                    span_obj,
                    "end",
                    output={"status": status, "elapsed_ms": elapsed_ms, "error": error},
                )

    def event(self, event_name: str, **metadata: Any) -> None:
        if not self.enabled:
            return
        payload = {
            "trace_id": self.trace_id,
            "trace": self.trace_name,
            "event": event_name,
            "meta": metadata,
        }
        print(f"[trace] {json.dumps(payload, sort_keys=True)}")
        if self.trace_obj is not None:
            _safe_call(self.trace_obj, "event", name=event_name, metadata=metadata or None)

    def finish(self, status: str = "ok", **metadata: Any) -> int:
        elapsed_ms = int((time.perf_counter() - self.started_at) * 1000)
        if self.enabled:
            payload = {
                "trace_id": self.trace_id,
                "trace": self.trace_name,
                "status": status,
                "elapsed_ms": elapsed_ms,
                "meta": metadata,
            }
            print(f"[trace] {json.dumps(payload, sort_keys=True)}")
        if self.trace_obj is not None:
            _safe_call(
                self.trace_obj,
                "update",
                output={"status": status, "elapsed_ms": elapsed_ms},
                metadata=metadata or None,
            )
        return elapsed_ms


class Tracer:
    def __init__(
        self,
        enabled: bool = True,
        host: str = "",
        public_key: str = "",
        secret_key: str = "",
    ) -> None:
        self.enabled = enabled
        self.host = host.strip()
        self.public_key = public_key.strip()
        self.secret_key = secret_key.strip()
        self.client: Any | None = None

        if self.enabled and self.public_key and self.secret_key and Langfuse is not None:
            try:
                kwargs: dict[str, Any] = {
                    "public_key": self.public_key,
                    "secret_key": self.secret_key,
                }
                if self.host:
                    kwargs["host"] = self.host
                self.client = Langfuse(**kwargs)
                print("[langfuse] enabled")
            except Exception as exc:
                print(f"[langfuse] init_failed error={exc}")
                self.client = None

    def start_trace(self, name: str, trace_id: str | None = None) -> TraceSession:
        resolved_trace_id = trace_id or str(uuid.uuid4())
        trace_obj = None
        if self.client is not None:
            trace_obj = _safe_call(self.client, "trace", id=resolved_trace_id, name=name)
        return TraceSession(
            trace_name=name,
            trace_id=resolved_trace_id,
            enabled=self.enabled,
            trace_obj=trace_obj,
        )

    def submit_feedback(
        self,
        trace_id: str,
        score: int,
        comment: str | None = None,
        name: str = "user_feedback",
    ) -> bool:
        if not self.enabled or self.client is None:
            return False

        payload: dict[str, Any] = {
            "name": name,
            "trace_id": trace_id,
            "value": score,
        }
        if comment:
            payload["comment"] = comment

        submitted = _safe_call(self.client, "score", **payload)
        return submitted is not None

    def shutdown(self) -> None:
        if self.client is None:
            return
        _safe_call(self.client, "flush")
        _safe_call(self.client, "shutdown")


def get_tracer() -> Tracer:
    return Tracer(
        enabled=settings.langfuse.enabled,
        host=settings.langfuse.host,
        public_key=settings.langfuse.public_key,
        secret_key=settings.langfuse.secret_key,
    )
