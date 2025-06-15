import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine


DB_CONNECTION = os.getenv("db_connection")

class Database:
    def __init__(self, db_conn):
        self.engine = create_engine(url=db_conn,
                                    poolclass=NullPool,
                                    connect_args={"timeout": 15})
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

azdb = Database(DB_CONNECTION)


