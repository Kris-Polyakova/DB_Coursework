import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship
from telebot.handler_backends import State, StatesGroup

Base = declarative_base()

class InitDict(Base):
    """ Database table class. Used to store the main group of words."""

    __tablename__ = 'initial_dictionary'
    id = sq.Column(sq.Integer, primary_key=True)
    eng_word = sq.Column(sq.String(length=30), nullable=False)
    ru_word = sq.Column(sq.String(length=35), nullable=False)

class User(Base):
    """ Database table class. Used to store user data."""

    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    user_chat_id = sq.Column(sq.Integer, nullable=False)
    user_step = sq.Column(sq.Boolean, default=False, nullable=False)
    
class UsersDict(Base):
    """ Database table class. Used to store user's personal word pairs."""
    
    __tablename__ = 'users_dictionary'
    id = sq.Column(sq.Integer, primary_key=True)
    eng_word = sq.Column(sq.String(length=30), nullable=False)
    ru_word = sq.Column(sq.String(length=35), nullable=False)
    id_user = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)
    user = relationship(User, backref="user")
    
class Command:
    """ Class for storing command names."""
    
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    
class MyStates(StatesGroup):
    """ Class for storing state variables."""
    
    target_word = State()
    translate_word = State()
    another_words = State()