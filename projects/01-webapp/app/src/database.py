import os
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DB_CONNECTION = os.getenv("db_connection", "sqlite:///./task.db")

class Database:
    def __init__(self, db_conn):
        self.engine = create_engine(url=db_conn,
                                    poolclass=NullPool,
                                    connect_args={"timeout": 15},
                                    echo=False)
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)


    def get_db(self):
        try:
            db = self.session()
            yield db
        finally:
            db.close()

    @property
    def conn(self):
        return self.engine.connect()

Base = declarative_base()
azdb = Database(DB_CONNECTION)


