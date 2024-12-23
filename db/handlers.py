import json
from langdetect import detect

from db.models import Base, Word, User, UserWord
from sqlalchemy import func

def create_tables(engine):
    """ Function for creating tables in a database."""

    Base.metadata.create_all(engine)


def add_data_from_file(session, filename=str):
    """ Function for add data into the table InitDict from the json file"""
    query = session.query(Word.id).filter(Word.id == 1)
    
    if bool(*query) == False:
        with open (filename, 'r', encoding = 'utf-8') as f:
            data = json.load(f)
            for record in data:
                model = {
                    'initial_dictionary': Word,
                }[record.get('model')]
                session.add(model(id=record.get('pk'), **record.get('fields')))
        session.commit()
    
    
def get_user_data(id_user, session):
    """ Function to get user data from the database."""

    query = ((session.query(User.user_chat_id, User.user_step))
             .select_from(User).filter(User.user_chat_id == id_user))
    return query

def add_standart_words(cid, session):
    query = session.query(Word.id).filter(Word.is_standart == True)
    for q in query:
        new_user_word = UserWord(id_user = get_db_user_id(cid, session), 
                                 id_word = q.id)
        session.add(new_user_word)
        session.commit()

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
    

def get_main_pair(cid, session):
    """ Function to get target pair."""
    query = (session.query(Word.eng_word, Word.ru_word).join(UserWord).
             filter(UserWord.id_user == get_db_user_id(cid, session))
             .order_by(func.random()).first())
    return query
    

def get_others_words(cid, target_word, session):
    """ Function to get four incorrect answer options from a database."""
    
    others = []
    counter = 0
    while counter<5 or len(others)<4:
        counter += 1
        query = (session.query(Word.eng_word).join(UserWord)
        .filter(UserWord.id_user == get_db_user_id(cid, session))
        .order_by(func.random()).first())
        if str(*query) != target_word and str(*query) not in others:
            others.append(str(*query))
        
    return others

def get_word_info(session, word):
    if detect(word) != 'ru':
        q_word = Word.eng_word
    else:
        q_word = Word.ru_word
    query = session.query(Word).filter(q_word == word)
    
    if (bool(*query)) != False:
        for q in query:
            return q.id, q.is_standart
    else:
        return False

def get_relationship_word(session, id_word):
    query = session.query(UserWord).filter(UserWord.id_word == id_word)
    if (bool(*query)) != False:
        for q in query:
            return q.id
    else:
        return False
    
def check_adds(session, en_word, ru_word):
    query = session.query(Word).filter(Word.eng_word == en_word 
                                       and Word.ru_word == ru_word)
    if (bool(*query)) == False:
        return False
    else:
        for q in query:
            return q.id

def check_user_word(session, id_user, id_word):
    query = session.query(UserWord.id).filter(UserWord.id_word == id_word 
                                              and UserWord.id_user == id_user)
    if (bool(*query)) == False:
        return False

def get_last_id(session, base):
    last = session.query(base).order_by(base.id.desc()).first()
    return last.id