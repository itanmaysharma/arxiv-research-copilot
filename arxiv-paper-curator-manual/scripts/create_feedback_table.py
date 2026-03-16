from src.db.base import Base
from src.db.session import engine
from src.models import Feedback  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Feedback table created/verified.")


if __name__ == "__main__":
    main()
