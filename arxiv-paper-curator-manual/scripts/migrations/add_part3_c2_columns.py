from sqlalchemy import text

from src.db.session import engine


SQL_STATEMENTS = [
    "ALTER TABLE papers ADD COLUMN IF NOT EXISTS parser_metadata_json TEXT",
    "ALTER TABLE paper_chunks ADD COLUMN IF NOT EXISTS section_title TEXT",
    "ALTER TABLE paper_chunks ADD COLUMN IF NOT EXISTS section_order INTEGER",
]


def main() -> None:
    with engine.begin() as conn:
        for stmt in SQL_STATEMENTS:
            conn.execute(text(stmt))
    print("P3-C2 schema columns ensured.")


if __name__ == "__main__":
    main()
