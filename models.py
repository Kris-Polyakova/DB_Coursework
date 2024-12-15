import json
import random
import os.path

from dotenv import load_dotenv
from сlasses import InitDict, User, UsersDict, Command, MyStates, Base

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage


def get_config():
    """ Function to get DSN and token. Gets data from file 'config.env'."""

    dotenv_path = 'config.env'
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    database = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_USER_PASSWORD')
    DSN = f"postgresql://{user}:{password}@localhost:5432/{database}"
    token_bot = os.getenv('TG_TOKEN')
    return DSN, token_bot

    
def create_tables(engine):
    """ Function for creating tables in a database."""

    Base.metadata.create_all(engine)

    
def add_data_from_file(session, filename=str):
    """ Function for add data into the table InitDict from the json file"""

    with open (filename, 'r', encoding = 'utf-8') as f:
        data = json.load(f)
        for record in data:
            model = {
                'initial_dictionary': InitDict,
            }[record.get('model')]
            session.add(model(id=record.get('pk'), **record.get('fields')))
    session.commit()
    

def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


def get_user_data(id, session):
    """ Function to get user data from the database."""

    query = ((session.query(User.user_chat_id, User.user_step))
             .select_from(User).filter(User.user_chat_id == id))
    return query


def get_user_step(uid, session):
    """ Function to get information about user steps."""

    query = get_user_data(uid, session)
    if bool(*query) == True:
        for q in query:
           return int(q.user_step)
    else:
        new_user = User(user_chat_id = uid, user_step = False)
        session.add(new_user)
        session.commit()
        print("New user detected, who hasn't used \"/start\" yet")
        return 0
    

def get_db_user_id(cid, session):
    """ Function for getting user db ID by telegtam user ID or chat ID."""

    query_user = (session.query(User.id).select_from(User)
                  .filter(User.user_chat_id == cid))
    for qu in query_user:
        return qu.id
    

def add_init_words(cid, session):
    """ Function to add a basic list of words for the user."""

    query = (session.query(InitDict.eng_word, InitDict.ru_word)
             .select_from(InitDict))
    for q in query:
        word_pair = UsersDict(eng_word=q.eng_word, ru_word=q.ru_word, 
                              id_user=get_db_user_id(cid, session))
        session.add(word_pair)
      
        
def get_main_pair(cid, session):
    """ Функция для получения рандомного таргет слова 
    и его перевода из базы данных.
    """

    query = (session.query(UsersDict.eng_word, UsersDict.ru_word)
             .filter(UsersDict.id_user == get_db_user_id(cid, session)))
    end = int(query.count()) - 1
    r = random.randint(0, end)
    return query[r]


def get_others_words(cid, target_word, session):
    """ Function to get four incorrect answer options from a database."""

    query = (session.query(UsersDict.eng_word)
             .filter(UsersDict.id_user == get_db_user_id(cid, session)
                     , UsersDict.eng_word != target_word))
    end = int(query.count()) - 1
    others = []
    counter = 0
    while counter<5 or len(others)<4:
        counter += 1
        r = random.randint(0, end)
        word = str(*query[r])
        if word not in others:
            others.append(word)
    return others