import telebot
import psycopg2
import os
import logging
from telebot import types
from config import *
from flask import Flask, request


bot = telebot.TeleBot("5430424349:AAE8BVZQsdST-t9zstNWycSmYQ3lQmtQ0Ow")
server = Flask(__name__)
logger = telebot.logger
logger.setLevel(logging.DEBUG)
conn = psycopg2.connect(DB_URL, sslmode="require")
cursor = conn.cursor()

@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

def insert_part(part: int, user_id: int, username: str):
    cursor.execute('INSERT INTO user_part (user_id, part, username) VALUES (%s, %s, %s)', (user_id, part, username))
    conn.commit()

def update_part(user_id: int, part: int = None, current_quest: int = None):
    if part is not None:
        cursor.execute('UPDATE user_part SET part=%s WHERE user_id=%s', (part, user_id))
    if current_quest is not None:
        cursor.execute('UPDATE user_part SET current_quest_id=%s WHERE user_id=%s', (current_quest, user_id))
    conn.commit()

def get_part(user_id: int):
    cursor.execute('SELECT part FROM user_part WHERE user_id=%s', ([user_id]))
    conn.commit()
    return cursor.fetchall()[0][0]

def get_name_by_id(user_id: int):
    cursor.execute('SELECT username FROM user_part WHERE user_id=%s', [user_id])
    conn.commit()
    return cursor.fetchall()[0][0]

def get_admins():
    cursor.execute('SELECT name, id FROM admins')
    conn.commit()
    return cursor.fetchall()

def get_admin_by_id(id: int):
    cursor.execute('SELECT name FROM admins WHERE id=%s', [id])
    conn.commit()
    return cursor.fetchall()[0][0]

def check_null(aid: int):
    cursor.execute('SELECT user_id FROM admins WHERE id=%s', [aid])
    conn.commit()
    return cursor.fetchall()[0][0]

def set_uid_by_username(username: str, user_id: int):
    cursor.execute('UPDATE admins SET user_id=%s WHERE username=%s', (user_id, username))
    conn.commit()

def get_cur_quest(user_id: int):
    cursor.execute('SELECT current_quest_id FROM user_part WHERE user_id=%s', ([user_id]))
    conn.commit()
    return cursor.fetchall()[0][0]

def add_quest(user_id: int, question_type: int):
    cursor.execute('INSERT INTO questions (user_id, question_type, status) VALUES (%s, %s, 0) RETURNING id', (user_id, question_type))
    conn.commit()
    return cursor.fetchall()

def get_open_quests():
    cursor.execute('SELECT * FROM questions WHERE status=0')
    conn.commit()
    return cursor.fetchall()

def get_quest_by_id(id: int):
    cursor.execute('SELECT * FROM questions WHERE id=%s', [id])
    conn.commit()
    return cursor.fetchall()[0]

def update_quest(qid: int, question: str = None, subject: int = None, feelings: str = None, admin_id: int = None):
    if question is not None:
        cursor.execute('UPDATE questions SET question=%s WHERE id=%s', (question, qid))
    if subject is not None:
        cursor.execute('UPDATE questions SET subject=%s WHERE id=%s', (subject, qid))
    if feelings is not None:
        cursor.execute('UPDATE questions SET feelings=%s WHERE id=%s', (feelings, qid))
    if admin_id is not None:
        cursor.execute('UPDATE questions SET meet_id=%s WHERE id=%s', (admin_id, qid))
    conn.commit()

def get_quest_types():
    cursor.execute('SELECT id, question_type FROM question_types')
    conn.commit()
    return cursor.fetchall()

def get_quest_type_by_id(id: int):
    cursor.execute('SELECT question_type FROM question_types WHERE id=%s', [id])
    conn.commit()
    return cursor.fetchall()[0][0]

def update_quest_status(id: int):
    cursor.execute('UPDATE questions SET status=1 WHERE id=%s', [id])
    conn.commit()

def get_subj():
    cursor.execute('SELECT subject_name FROM subjects')
    conn.commit()
    return cursor.fetchall()

def update_admin_part(user_id: int, part: int):
    cursor.execute('UPDATE admins SET part=%s WHERE user_id=%s', (part, user_id))
    conn.commit()

def get_admin_part(username: str):
    cursor.execute('SELECT part FROM admins WHERE username=%s', [username])
    conn.commit()
    return cursor.fetchall()[0][0]

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    try:
        set_uid_by_username(message.from_user.username, message.from_user.id)
        item1 = ("Найти вопрос")
        item2 = ("Просмотреть все вопросы")
        item3 = ("Закрыть вопрос")
        markup.add(item1)
        markup.add(item2)
        markup.add(item3)
    except:
        try:
            get_part(message.from_user.id)
            update_part(message.from_user.id, part=0)
        except:
            insert_part(0, message.from_user.id, message.from_user.username)
        finally:
            item1 = types.KeyboardButton("Задать вопрос")
            markup.add(item1)
    bot.send_message(message.chat.id, 'Добро пожаловать', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text.strip() == 'Найти вопрос':
        update_admin_part(message.from_user.id, 1)
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.from_user.id, 'Какой id вопроса?', reply_markup=markup)
        return

    if message.text.strip() == 'Закрыть вопрос':
        update_admin_part(message.from_user.id, 2)
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.from_user.id, 'Какой id вопроса?', reply_markup=markup)
        return

    if message.text.strip() == 'Просмотреть все вопросы':
        quests = get_open_quests()
        for i in range(len(quests)):
            name = get_name_by_id(quests[i][1])
            if quests[i][3] is not None:
                msg = 'id вопроса: {}\nвопрос по предмету {}: {}\nощущения: {}\nтг для связи: {}'.format(quests[i][0], quests[i][3], quests[i][4], quests[i][5], name)
            elif quests[i][6] is not None:
                aname = get_admin_by_id(quests[i][6])
                msg = 'id вопроса: {}\nвопрос для встречи с {}: {}\nощущения: {}\nтг для связи: {}'.format(quests[i][0], aname, quests[i][4], quests[i][5], name)
            else:
                quest_type = get_quest_type_by_id(quests[i][2])
                msg = 'id вопроса: {}\n{}: {}\nощущения: {}\nтг для связи: {}'.format(quests[i][0], quest_type, quests[i][4], quests[i][5], name)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = ("Найти вопрос")
            item2 = ("Просмотреть все вопросы")
            item3 = ("Закрыть вопрос")
            markup.add(item1)
            markup.add(item2)
            markup.add(item3)
            bot.send_message(message.from_user.id, msg, reply_markup=markup)
        return

    if get_admin_part(message.from_user.username) == 1:
        update_admin_part(message.from_user.id, 0)
        quest = get_quest_by_id(int(message.text.strip()))
        name = get_name_by_id(quest[1])
        if quest[3] is not None:
            msg = 'id вопроса: {}\nвопрос по предмету {}: {}\nощущения: {}\nтг для связи: {}'.format(quest[0],
                                                                                                           quest[3],
                                                                                                           quest[4],
                                                                                                           quest[5],
                                                                                                           name)
        elif quest[6] is not None:
            aname = get_admin_by_id(quest[6])
            msg = 'id вопроса: {}\nвопрос для встречи с {}: {}\nощущения: {}\nтг для связи: {}'.format(
                quest[0], aname, quest[4], quest[5], name)
        else:
            quest_type = get_quest_type_by_id(quest[2])
            msg = 'id вопроса: {}\n{}: {}\nощущения: {}\nтг для связи: {}'.format(quest[0], quest_type,
                                                                                        quest[4], quest[5],
                                                                                        name)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = ("Найти вопрос")
        item2 = ("Просмотреть все вопросы")
        item3 = ("Закрыть вопрос")
        markup.add(item1)
        markup.add(item2)
        markup.add(item3)
        bot.send_message(message.from_user.id, msg, reply_markup=markup)
        return

    if get_admin_part(message.from_user.username) == 2:
        update_admin_part(message.from_user.id, 0)
        update_quest_status(int(message.text.strip()))
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = ("Найти вопрос")
        item2 = ("Просмотреть все вопросы")
        item3 = ("Закрыть вопрос")
        markup.add(item1)
        markup.add(item2)
        markup.add(item3)
        bot.send_message(message.chat.id, 'Добро пожаловать', reply_markup=markup)
        return

    if message.text.strip() == 'Задать вопрос':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        quest_types = get_quest_types()
        items = []
        for i in range(0, len(quest_types)):
            items.append(types.KeyboardButton(quest_types[i][1]))
            markup.add(items[i])
        update_part(message.from_user.id, part=1)
        bot.send_photo(message.from_user.id, 'https://lh3.googleusercontent.com/12GJ5HEGMWk6JnkUdWjhthXakfP02ImT1Uuk-5UM_wrX2m2MWOtcxCbj8BvEZnI6HKlkDw1SqZkdS-kWwbTBJKCm6mFouY74-LdOarZKlAZjRT6RSFWMe4TP3DJKTXiBWg=w303',
                       caption='Выберите тип вопроса', reply_markup=markup)
        return

    if get_part(message.from_user.id) == 1:
        try:
            try:
                quest_types = get_quest_types()
                columns = list(zip(*quest_types))
                id = columns[1].index(message.text.strip())
                qid = add_quest(message.from_user.id, id)
                update_part(message.from_user.id, current_quest=qid[0][0])
            except:
                admins = get_admins()
                columns = list(zip(*admins))
                id = columns[1][columns[0].index(message.text.strip())]
                qid = get_cur_quest(message.from_user.id)
                update_quest(qid, admin_id=id)
                aid = check_null(id)
                if aid is not None:
                    msg = 'Кто-то хочет с вами встретиться! Вот его ник в telegram: {}, id запроса - {}'.format(message.from_user.username, qid)
                    bot.send_message(aid, msg)
        except:
            subjects = get_subj()
            columns = list(zip(*subjects))
            id = columns[0].index(message.text.strip())
            qid = get_cur_quest(message.from_user.id)
            update_quest(qid, subject=id)
        finally:
            if message.text.strip() == 'вопрос по предмету':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                subjects = get_subj()
                items = []
                for i in range(0, len(subjects)):
                    items.append(types.KeyboardButton(subjects[i][0]))
                    markup.add(items[i])
                bot.send_photo(message.from_user.id,
                               'https://lh4.googleusercontent.com/kicmRl8qp_PCq9LP_zk9-clHpE9LhMom4ZgC3MUnDuZDwrmNIcupGim-s4qwx9QUTWS3_oe_6nV-nDEETLZQhXdDr15tshXCCqZI0T-qkPQ-Tmt0qpam87wYDuAqD0A7Iw=w333',
                               caption='Какой предмет?', reply_markup=markup)
                return
            elif message.text.strip() == 'нужна личная встреча с кем-то из дп2':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                admins = get_admins()
                items = []
                for i in range(0, len(admins)):
                    items.append(types.KeyboardButton(admins[i][0]))
                    markup.add(items[i])
                bot.send_photo(message.from_user.id,
                               'https://lh6.googleusercontent.com/uhAWHT2wOzTg6H2ZYw9wTuDgle6VNcOkjFaHKKd52tlh-DbAUxppL54aw8TpDs5XMNOg0UDk_3V3JFKf2s1ehH2w6HhgdbXdug0N0xFzswN8E-KhB-qjZjFM1AOXpIv5VQ=w387',
                               caption='с кем ты хочешь встретиться?', reply_markup=markup)
                return

            else:
                update_part(message.from_user.id, part=2)
                markup = types.ReplyKeyboardRemove()
                bot.send_photo(message.from_user.id,
                               'https://lh3.googleusercontent.com/YsQxzOAoF1Sb9ofp95iUeIgLRvbqlApN7_VjZ-QPPb7wwVn-IetRaXbRBUXsWZZ-p1p_vYmmEAzhZYm60Mt31dsCXebHD3TaIKLNICWA0tbNkSlvk5pLPVVQtS56GNBXzw=w307',
                               caption='Какой у тебя вопрос?', reply_markup=markup)
                return
    if get_part(message.from_user.id) == 2:
        try:
            qid = get_cur_quest(message.from_user.id)
            update_quest(qid, question=message.text.strip())
        finally:
            markup = types.ReplyKeyboardRemove()
            update_part(message.from_user.id, part=3)

            bot.send_photo(message.from_user.id,
                           'https://lh6.googleusercontent.com/lw82EDuFWO4jzI_K9cBhi89OOO3ZxpJhxY5-ndvGhPzA4cVdpsXqsPEL1DI0jFItSgq2ldibdcQtn4v1raT4v6UgGTLd5urMeSggXNF1oxaCwCmVaHWoP6PozFQDOudG2A=w282',
                           caption='как вообще день проходит, как себя чувствуешь? все нормально?', reply_markup=markup)
            return
    if get_part(message.from_user.id) == 3:
        qid = get_cur_quest(message.from_user.id)
        update_quest(qid, feelings=message.text.strip())
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Задать вопрос")
        markup.add(item1)
        update_part(message.from_user.id, part=0)
        bot.send_photo(message.from_user.id,
                       'https://lh6.googleusercontent.com/LWPEoQ8yebjLXQpt_KseWknDwDb22jTTXm8_vtonTajw6CiygfG2GzW531eDdl2VXxBsvotyTSVsOFWyGamMmOZ27HaAikd8Ni6-BrNKa2ffOo6y6VUhQ6yf0YBrHaLvoA=w564',
                       caption='спасибо за твой вопрос! очень скоро наши админы ответят на него в канале или лично :)', reply_markup=markup)
        return

bot.polling(none_stop=True, interval=0)