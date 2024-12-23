import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Word(Base):
    """ Database table class. Used to store all words."""

    __tablename__ = 'word'
    id = sq.Column(sq.Integer, primary_key=True)
    eng_word = sq.Column(sq.String(length=30), nullable=False)
    ru_word = sq.Column(sq.String(length=35), nullable=False)
    is_standart = sq.Column(sq.Boolean, default=True, nullable=False)

class User(Base):
    """ Database table class. Used to store user data."""

    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    user_chat_id = sq.Column(sq.Integer, nullable=False)
    user_step = sq.Column(sq.Boolean, default=False, nullable=False)
    

    
class UserWord(Base):
    """ Database table class. 
    Used to storing the user's attitude to the word in dictionary.
    """
    
    __tablename__ = 'user_word'
    id = sq.Column(sq.Integer, primary_key=True)
    id_user = sq.Column(sq.Integer, sq.ForeignKey("user.id"))
    user = relationship(User, backref="user")
    id_word = sq.Column(sq.Integer, sq.ForeignKey("word.id"))
    word = relationship(Word, backref="word")