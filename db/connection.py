import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker

from src.get_config import get_config

engine = sq.create_engine(get_config()[0])
Session = sessionmaker(bind=engine)
session = Session()
