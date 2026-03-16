from src.services.langfuse.tracer import Tracer


def test_tracer_generates_trace_id_and_elapsed() -> None:
    tracer = Tracer(enabled=False)
    trace = tracer.start_trace("ask")
    with trace.span("work"):
        pass
    elapsed = trace.finish(status="ok")

    assert isinstance(trace.trace_id, str)
    assert trace.trace_id
    assert elapsed >= 0


def test_submit_feedback_returns_false_when_client_missing() -> None:
    tracer = Tracer(enabled=False)
    ok = tracer.submit_feedback(trace_id="trace-1", score=4, comment="good")
    assert ok is False


def test_shutdown_is_safe_without_client() -> None:
    tracer = Tracer(enabled=False)
    tracer.shutdown()
