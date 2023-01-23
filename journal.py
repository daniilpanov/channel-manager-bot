import datetime

from DB import db
from ENV import env
from telebot import TeleBot

bot = TeleBot(env.get('journal_bot_token'), parse_mode='Markdown')


def get_journal_for(form, day=None):
    if day:
        return db.query(f'SELECT * FROM journal WHERE form=\'{form}\' and `dayofweek`={day} ORDER BY orderofitem',
                        simple=False) \
               or (None if bool(db.query(f'SELECT id FROM journal WHERE form=\'{form}\'')) else False)
    else:
        return db.query(f'SELECT * FROM journal WHERE form=\'{form}\' ORDER BY `dayofweek`, orderofitem', simple=False) or False


def msg(form, day):
    data = get_journal_for(form, day)
    if data is None:
        return 'Похоже, в этот день мы не учимся'
    elif data is False:
        return 'Расписание для этого класса ещё не занесено :('
    else:
        text = "Расписание:\n"
        for item in data:
            text += str(item['orderofitem']) + '. ' + item['name']
            if item['cab']:
                text += ' (в кабинете №' + str(item['cab']) + ')'
            text += "\n"
        return text


@bot.message_handler(commands=['now'])
def current_lesson(message):
    bot.reply_to(message, 'Эта команда пока не реализована')


@bot.message_handler(func=lambda x: True)
def journal_today(message):
    text = message.text
    if len(text) <= 1 or text[0] != '/':
        bot.reply_to(message, 'Бот не распознал ваши карякули -_-')
        return

    text = text[1:]
    if len(text.split(' ')) > 1:
        form, day = text.split(' ')
        bot.reply_to(message, msg(form, day))
    elif datetime.datetime.now().weekday() == 6:
        bot.reply_to(message, 'Сегодня воскресенье, иди спать')
    else:
        bot.reply_to(message, msg(text, datetime.datetime.now().weekday() + 1))


bot.infinity_polling()
