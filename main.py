from telebot import TeleBot
from json import JSONDecoder

# config
token = '5831634929:AAHyOSz9Xr7yv6_p--gV1l68H-0sXDyHDck'
bot = TeleBot(token, parse_mode='Markdown')
# file with dialogs
with open('dialogs.json', encoding='UTF-8') as datafile:
    raw_data = ''.join(list(datafile))
    dialogs = JSONDecoder().decode(raw_data)


# current state
current_command_history = []
data = []


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
        repl += args
    for key in repl:
        sentence = sentence.replace('{' + key + '}', repl[key](message))
    
    return sentence


# decorator helps to clean up the commands history
def history_decorator(func):
    def wrapper(message):
        global current_command_history
        current_command_history = [message]
        if func(message):
            current_command_history = []
    return wrapper


# send usual reply
def reply(message, msg, parsing=True):
    if hasattr(msg, 'text'):
        msg = msg.text
    bot.send_message(message.chat.id, parse_sentence(msg, message) if parsing else msg)


# engine (commands list)
@history_decorator
def welcome_message(message):
    reply(message, get_dialog('start')[0])
    return True


@history_decorator
def help_message(message):
    dialogue = get_dialog('help')
    for msg in dialogue:
        reply(message, msg)
    return True


@history_decorator
def cancel_command(message):
    reply(message, get_dialog('cancel')[1])
    return True


@history_decorator
def back_command(message):
    reply(message, get_dialog('back')[1])
    return True


@history_decorator
def watch_command(message):
    dialogue = get_dialog('watch')[0]
    reply(message, dialogue)
    current_command_history.append(dialogue)

    dialogue = get_dialog('watch')[1]
    reply(message, dialogue)
    current_command_history.append(dialogue)

    return False


@history_decorator
def endwatch_command(message):
    pass


@history_decorator
def showactive_command(message):
    return True


@history_decorator
def showinactive_command(message):
    return True


@history_decorator
def showall_command(message):
    return True


@history_decorator
def search_command(message):
    pass


@history_decorator
def status_command(message):
    return True


@history_decorator
def allstatuses_command(message):
    return True


@history_decorator
def notifications_command(message):
    return True


@history_decorator
def stopnotifications_command(message):
    return True


# core - functions mapping and routing
# the map
map = {
    'start': welcome_message,
    'help': help_message,
    'cancel': cancel_command,
    'back': back_command,
    'watch': watch_command,
    'endwatch': endwatch_command,
    'showactive': showactive_command,
    'showinactive': showinactive_command,
    'showall': showall_command,
    'search': search_command,
    'status': status_command,
    'allstatuses': allstatuses_command,
    'notifications': notifications_command,
    'stopnotifications': stopnotifications_command,
}


# the main router
@bot.message_handler(commands=list(map.keys()))
def route(message):
    if message.text[0] == '/':
        command = message.text.split()[0][1:]
        user = message.from_user.username if hasattr(message.from_user, 'username') else message.from_user.id
        print(f'User {user} sent the command {command}')
        map[command](message)


# the secondary router
@bot.message_handler(func=lambda msg: True)
def all_messages(message):
    global current_command_history
    global data
    command = message.text.split()[0][1:]
    print(current_command_history)
    # if secondary router is not initialised
    if not current_command_history:
        reply(message, get_dialog('__unknown'))
    # cancel the command
    elif command == 'cancel':
        reply(message, get_dialog('cancel')[0])
        current_command_history = []
    # go back
    elif command == 'back':
        reply(message, get_dialog('back')[0])
        current_command_history.pop()
        if not current_command_history:
            reply(message, get_dialog('cancel')[0])
        else:
            current_command_history.pop()
            data.pop()
            reply(message, current_command_history[-1], False)
    else:
        state = len(current_command_history)
        # starts new static routing
        match current_command_history[0].text:
            case '/watch':
                if state > 16:
                    reply(message, parse_sentence(get_dialog('watch')[8], {'alliance_name': data[0]}))
                    current_command_history = []
                    # do something...
                    data = []
                else:
                    current_command_history.append(message)
                    data.append(message)
                    dialogue = parse_sentence(get_dialog('watch')[len(data) + 2], message)
                    current_command_history.append(dialogue)
                    reply(message, dialogue)
            case _:
                reply(message, get_dialog('__unknown'))


# start
bot.infinity_polling()
