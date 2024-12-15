import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker

from models import *

import random

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from telebot.types import ReplyKeyboardRemove

from сlasses import Command, User, UsersDict, MyStates, Base


engine = sq.create_engine(get_config()[0])
Session = sessionmaker(bind=engine)
session = Session()

create_tables(engine)
add_data_from_file(session, 'initial_dictionary_data.json')

print('Start telegram bot...')

state_storage = StateMemoryStorage()
bot = TeleBot(get_config()[1], state_storage=state_storage)


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    """ Function for creating quiz cards."""

    cid = message.chat.id
    query = get_user_data(cid, session)
    if bool(*query) == False:
        new_user = User(user_chat_id = cid, user_step = True)
        session.add(new_user)
        add_init_words(cid, session)
        session.commit()
        bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []
    word_pair = get_main_pair(cid, session)
    target_word = word_pair[0]
    translate = word_pair[1]
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = get_others_words(cid, target_word, session)
    
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)
    
    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)
    

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    """ Function for deleting a word from the user's personal dictionary."""

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        cid = message.chat.id
        word = data['target_word']
        query = session.query(UsersDict).filter(UsersDict.eng_word == word 
               and UsersDict.id_user == get_db_user_id(cid, session)).delete()
        session.commit()
        bot.send_message(cid, f"Слово, {word} удалено.")

  
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def request_add_words(message):
    """ Function for the bot to send a question to the user 
    and call the function to add a word.
    """

    cid = message.chat.id
    send = bot.send_message(cid, "Отправь слово на английском языке "
                                 "и его перевод.")
    send = bot.send_message(cid, "Пример: cat - кошка")
    bot.register_next_step_handler(send, add_user_words)
    
def add_user_words(message):
    """ Function for checking user data 
    and entering data into the user's personal dictionary.
    """
    
    cid = message.chat.id
    words = message.text.lower()
    if len(words.split("-")) == 2:
        eng_word = words.split("-")[0]
        ru_word = words.split("-")[1]
        word_pair = UsersDict(eng_word=eng_word.replace(' ', ''), 
                              ru_word=ru_word.replace(' ', ''), 
                              id_user=get_db_user_id(cid, session))
        session.add(word_pair)
        session.commit()
        bot.send_message(cid, 
                         f"Пара, {eng_word.replace(' ', '')} - {ru_word.replace(' ', '')} добавлена в твой словарь.")
    else:
        bot.send_message(cid, "Допущена ошибка!" 
                         " Проверь, между словами нужен дефис.")
        request_add_words(message)
        

@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    """ The function checks the selected answer option, 
    responds to the user.
    """

    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово", 
                             f"🇷🇺{data['translate_word']}")
           
    bot.send_message(message.chat.id, hint, reply_markup=markup)
    

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)
session.close()