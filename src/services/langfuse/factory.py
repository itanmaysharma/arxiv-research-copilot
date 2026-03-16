from functools import lru_cache

from src.services.langfuse.tracer import Tracer, get_tracer


@lru_cache(maxsize=1)
def make_tracer_service() -> Tracer:
    return get_tracer()
