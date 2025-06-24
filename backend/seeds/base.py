from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

class BaseSeeder:
    def __init__(self):
        self.engine = create_engine(str(settings.DATABASE_URL))
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def run(self):
        with self.SessionLocal() as session:
            self.seed(session)
            session.commit()
    
    def seed(self, session):
        raise NotImplementedError