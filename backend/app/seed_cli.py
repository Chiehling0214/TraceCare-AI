from app.core.database import SessionLocal, create_all
from app.seed.synthetic import seed_synthetic_data


def main() -> None:
    create_all()
    db = SessionLocal()
    try:
        result = seed_synthetic_data(db)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
