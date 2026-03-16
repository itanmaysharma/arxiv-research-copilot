from src.db.base import Base
from src.db.session import engine
from src.models import Feedback, Paper, PaperChunk  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified.")


if __name__ == "__main__":
    main()
