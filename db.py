from sqlalchemy import create_engine, Column, Integer, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./checkboxes.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Checkbox(Base):
    __tablename__ = "checkboxes"

    id = Column(Integer, primary_key=True, index=True)
    checked = Column(Boolean, default=False, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        count = db.query(Checkbox).count()
        if count == 0:
            for i in range(1, 501):
                db.add(Checkbox(id=i, checked=False))
            db.commit()
    finally:
        db.close()