from telebot import TeleBot
from json import JSONDecoder

# config
token = '5831634929:AAHyOSz9Xr7yv6_p--gV1l68H-0sXDyHDck'
bot = TeleBot(token, parse_mode='Markdown')
# file with dialogs
with open('dialogs.json', encoding='UTF-8') as datafile:
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
        repl |= args
    for key in repl:
        sentence = sentence.replace('{' + key + '}', repl[key](message) if callable(repl[key]) else repl[key])
    
    return sentence


# Two previous functions together
def get_dialog_with_parsing(command, index, message, args=None):
    return parse_sentence(get_dialog(command)[index], message, args)


# send usual reply
def reply(message, msg, parsing=True):
    if hasattr(msg, 'text'):
        msg = msg.text
    bot.send_message(message.chat.id, parse_sentence(msg, message) if parsing else msg)


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
@bot.message_handler()
def route(message):
    global current

    if message.from_user.id in current and current[message.from_user.id]:
        if current[message.from_user.id].result:
            current[message.from_user.id] = None
            return route(message)
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
