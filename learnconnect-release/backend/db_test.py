from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import declarative_base, sessionmaker
from config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False,
)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
# Base = declarative_base()
#
#
# def get_db():
#     db = SessionLocal()
#     print(db)
#     try:
#         yield db
#     finally:
#         db.close()


from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(tables)

from models import Doubt, User
rows = session.query(Doubt).all()
print()

with engine.connect() as conn:
    rows = conn.execute(select(Doubt)).fetchall()
    for r in rows:
        print(dict(r._mapping))


# from sqlalchemy.orm import Session
#
# session = Session(engine)
#
# row = session.query(User).filter(User.email == "abc@abc.com").first()
#
# if row:
#     row.password_hash = "$pbkdf2-sha256$29000$.T9nbK0V4nxPyZkTIiRECA$vvhFmWkmZARmKmQ0GmPwqkBZaw4hLkZgQPbmguF1PcA"   # update column
#     session.commit()
# else:
#     print("User not found")

# if row:
#     print(row)
#     session.delete(row)
#     session.commit()

# with engine.connect() as conn:
#     rows = conn.execute(select(User)).fetchall()
#     for r in rows:
#         print(dict(r._mapping))


# from sqlalchemy.orm import Session
#
# session = Session(engine)
#
# from models import Group
# rows = session.query(Group).all()
# for row in rows:
#     print(dict(row._mapping))
#     # for i in row:
#     #     print(i)
