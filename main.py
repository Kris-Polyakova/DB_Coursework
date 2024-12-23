import random

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage

from db.connection import session, engine
import db.handlers as dbh
from db.models import User, UserWord, Word
from src.get_config import get_config
from src.show import show_hint, show_target
from classes.command import Command
from classes.my_states import MyStates


dbh.create_tables(engine)
dbh.add_data_from_file(session, 'initial_dictionary_data.json')

print('Start telegram bot...')

state_storage = StateMemoryStorage()
bot = TeleBot(get_config()[1], state_storage=state_storage)


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    """ Function for creating quiz cards."""

    cid = message.chat.id
    query = dbh.get_user_data(cid, session)
    if bool(*query) == False:
        new_user = User(user_chat_id = cid, user_step = False)
        session.add(new_user)
        dbh.add_standart_words(cid, session)
        session.commit()
        bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []
    word_pair = dbh.get_main_pair(cid, session)
    
    target_word = word_pair[0]
    translate = word_pair[1]
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = dbh.get_others_words(cid, target_word, session)
    
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
def request_add_words(message):
    """ function for the bot to send a question to the user 
    and call the function to delete a word.
    """

    cid = message.chat.id
    send = bot.send_message(cid, "Какое слово нужно удалить?")
    bot.register_next_step_handler(send, delete_word)

def delete_word(message):
    """ Function for deleting a word from the user's personal dictionary."""

    with bot.retrieve_data(message.from_user.id, message.chat.id):
        cid = message.chat.id
        word = message.text.lower()
        word_info = dbh.get_word_info(session, word)
        
        if word_info != False:
            if word_info[1] == False:
                del_user_word = (session.query(UserWord)
                                 .filter(UserWord.id_word == word_info[0] 
                                  and UserWord.id_user == cid).delete())
                session.flush()
                if dbh.get_relationship_word(session, word_info[0]) == False:
                    del_word = (session.query(Word)
                                .filter(Word.id == word_info[0]).delete())
                  
            if word_info[1] == True:
                del_user_word = (session.query(UserWord)
                                 .filter(UserWord.id_word == word_info[0] 
                                 and UserWord.id_user == cid).delete())
                session.flush() 
            session.commit()      
            bot.send_message(cid, f"Слово, {word} удалено.")        
        else:
            bot.send_message(cid, f"Слова, {word} нет в твоём словаре.")
         

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def request_add_words(message):
    """ Function for the bot to send a question to the user 
    and call the function to add a word.
    """

    cid = message.chat.id
    send = bot.send_message(cid, "Отправь слово, которое хочешь добавить "
                                 "и его перевод.")
    send = bot.send_message(cid, "Пример: cat - кошка")
    bot.register_next_step_handler(send, add_user_words)
    
def add_user_words(message):
    """ Function for checking user data 
    and entering data into the user's personal dictionary.
    """
    
    cid = message.chat.id
    user_id = dbh.get_db_user_id(cid, session)
    words = message.text.lower()
    
    if len(words.split("-")) == 2:
        eng_word = words.split("-")[0].strip()
        ru_word = words.split("-")[1].strip()
        id_word = dbh.get_last_id(session, Word) + 1
        check_info = dbh.check_adds(session, eng_word, ru_word)
        
        if check_info == False:
            word_pair = Word(id = id_word,
                              eng_word=eng_word, 
                              ru_word=ru_word, 
                              is_standart=False)
            session.add(word_pair)
            id_user_word = dbh.get_last_id(session, UserWord) + 1
            user_word = UserWord(id=id_user_word, 
                                 id_user=user_id, id_word=id_word)
            session.add(user_word)
            session.flush()
            bot.send_message(cid, 
                         f"Пара, {eng_word} - {ru_word} "
                         f"добавлена в твой словарь.")
        else:
            if dbh.check_user_word(session, user_id, check_info) == False:
                user_word = UserWord(id=id_user_word, 
                                     id_user=user_id, id_word = check_info)
                session.add(user_word)
                session.flush()
                bot.send_message(cid, 
                         f"Пара, {eng_word} - {ru_word} "
                         f"добавлена в твой словарь.")
            else:
                bot.send_message(cid, "Такое сочетание слов "
                                 "уже есть в твоём словаре!")
        session.commit()
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