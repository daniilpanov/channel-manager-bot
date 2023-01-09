import datetime

from telebot import TeleBot
from json import JSONDecoder

from DB import DB
from ENV import env

# config
token = env.get('bot_token')
bot = TeleBot(token, parse_mode='Markdown')
# file with dialogs
with open(env.get('dialogs'), encoding=env.get('dialogs_encoding') or 'UTF-8') as datafile:
    raw_data = ''.join(list(datafile))
    dialogs = JSONDecoder().decode(raw_data)


# helpful functions
# getting dialog item
def get_dialog(command):
    return dialogs[command]


# parsing dialog item (uses shortcodes)
def parse_sentence(sentence, message, args=None):
    repl = {
        'msg_name': lambda msg: msg.from_user.first_name
    }
    if args:
        repl = {**repl, **args}
    for key in repl:
        sentence = sentence.replace('{' + key + '}', repl[key](message) if callable(repl[key]) else repl[key])
    
    return sentence


# Two previous functions together
def get_dialog_with_parsing(command, index, message, args=None):
    return parse_sentence(get_dialog(command)[index], message, args)


# send usual reply
def reply(message, msg, parsing=True, parse_mode='Markdown'):
    if hasattr(msg, 'text'):
        msg = msg.text
    bot.send_message(message.chat.id, parse_sentence(msg, message) if parsing else msg, parse_mode=parse_mode)


# CORE - functions mapping and routing
# The map
MAP = dict()
# Current
current = dict()


# Register
def reg(command, function):
    global MAP
    MAP[command] = function


# Decorator (simple register)
def bot_func(func):
    reg(func.__name__.replace('_command', ''), func)


# ROUTER
# Watch to users activity
def active(message):
    user_info = DB.query(sql='SELECT * FROM users WHERE identification=%s', params=[message.from_user.id])
    now = datetime.datetime.now().isoformat()
    if user_info and len(user_info) > 0:
        DB.query(
            sql='UPDATE users SET last_active=%s WHERE id=%s',
            params=(now, user_info[0][0])
        )
    else:
        DB.query(
            sql='INSERT INTO users (nickname, identification, last_active) VALUE (%s, %s, %s)',
            params=(message.from_user.username, message.from_user.id, now)
        )


@bot.message_handler()
def route(message):
    global current

    if message.from_user.id in current and current[message.from_user.id]:
        if current[message.from_user.id].result:
            current[message.from_user.id] = None
            route(message)
            active(message)
        else:
            current[message.from_user.id].route(message)
    elif message.text[0] == '/':
        command = message.text.split()[0][1:]
        user = message.from_user.username if hasattr(message.from_user, 'username') else message.from_user.id
        print(f'User {user} sent the command {command}')
        if command in MAP:
            current[message.from_user.id] = MAP[command](message)
        else:
            reply(message, get_dialog('__unknown'))
    else:
        reply(message, get_dialog('__unknown'))

    active(message)
