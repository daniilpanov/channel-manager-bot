from config import reply, get_dialog, get_dialog_with_parsing, reg, bot_func, bot, current
from telebot import types


# This class uses for multiple commands
class Command:
    def __init__(self, message):
        # Initial message
        self.base_message = message
        # Data from user
        self.data = []
        # Current state of the dialog
        self.state = 0
        # The map of the questions
        self.map = []
        # The result
        self.result = False
        # The bot messages history
        self.history = dict()

    # Sub routing
    def route(self, message):
        if message.text.strip() == '/back':
            self.back(message)
        elif message.text.strip() == '/cancel':
            self.cancel(message)
        elif len(self.map) > self.state - 1:
            if self.map[self.state - 1](message):
                self.state += 1
        else:
            self.finish(message)

    # Custom message sending
    def reply(self, message, msg):
        if self.state not in self.history:
            self.history[self.state] = []
        self.history[self.state].append(msg)
        reply(message, msg)

    # Finish
    def finish(self, message):
        self.result = True

    # Interrupt
    def cancel(self, message):
        reply(message, get_dialog_with_parsing('cancel', 0, message))
        self.result = True

    # Back
    def back(self, message):
        if len(self.data) > 0:
            self.data.pop()
            self.state -= 1
            self.history.pop(self.state)
            reply(message, get_dialog_with_parsing('back', 0, message))
            for msg in self.history[self.state - 1]:
                reply(message, msg, False)
        else:
            self.cancel(message)


# Multi commands
def check_name(name):
    return True


class Watch(Command):
    def __init__(self, message):
        super().__init__(message)
        self.reply(message, get_dialog_with_parsing('watch', 0, message))
        self.reply(message, get_dialog_with_parsing('watch', 1, message))
        self.map = [
            self.name_desc,
            self.description_first_id,
            self.first_id_first_hash,
            self.first_hash_second_id,
            self.second_id_second_hash,
            self.second_hash_days,
        ]
        self.state += 1

    def name_desc(self, message):
        if not check_name(message.text):
            reply(message, get_dialog_with_parsing('watch', 9, message))
            return False
        self.data.append(message.text)
        self.reply(message, get_dialog_with_parsing('watch', 2, message))
        return True

    def description_first_id(self, message):
        if message.text != '-':
            self.data.append(message.text)
        self.reply(message, get_dialog_with_parsing('watch', 3, message))
        return True

    def first_id_first_hash(self, message):
        self.data.append(message.text)
        self.reply(message, get_dialog_with_parsing('watch', 4, message))
        return True

    def first_hash_second_id(self, message):
        self.data.append(message.text)
        self.reply(message, get_dialog_with_parsing('watch', 5, message))
        return True

    def second_id_second_hash(self, message):
        self.data.append(message.text)
        self.reply(message, get_dialog_with_parsing('watch', 6, message))
        return True

    def second_hash_days(self, message):
        self.data.append(message.text)
        self.reply(message, get_dialog_with_parsing('watch', 7, message))
        return True

    def finish(self, message):
        super().finish(message)
        self.reply(message, get_dialog_with_parsing('watch', 8, message, {'alliance_name': self.data[0]}))


class Endwatch(Command):
    def __init__(self, message):
        super().__init__(message)
        command, *data = message.text[1:].split()
        data = ' '.join(data)
        if not data:
            self.map = [
                self.inline_buttons,
                self.do_nothing,
            ]
            self.reply(message, get_dialog_with_parsing('endwatch', 7, message))
            self.state += 1
        else:
            self.map = [
                self.do_nothing,
            ]
            self.inline_buttons(message)
            self.state += 1

    def inline_buttons(self, message):
        if message.text[0] == '/':
            command, *data = message.text[1:].split()
            data = ' '.join(data)
        else:
            data = message.text

        alliance = self.check_alliance(data)
        if not alliance:
            reply(message, get_dialog_with_parsing('endwatch', 4, message))
            self.result = True
            return False
        keyboard = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(text=get_dialog_with_parsing('endwatch', 1, message), callback_data='11')],
            [types.InlineKeyboardButton(text=get_dialog_with_parsing('endwatch', 2, message, {'1': alliance[0]}),
                                        callback_data='10')],
            [types.InlineKeyboardButton(text=get_dialog_with_parsing('endwatch', 8, message, {'2': alliance[1]}),
                                        callback_data='01')],
            [types.InlineKeyboardButton(text=get_dialog_with_parsing('endwatch', 3, message), callback_data='00')],
        ])
        bot.reply_to(message, text=get_dialog_with_parsing('endwatch', 0, message), reply_markup=keyboard)
        self.state += 1
        return True

    def do_nothing(self):
        pass

    def check_alliance(self, alliance):
        return ['dsf', 'sdfds']


def init():
    # Register simple commands
    # Welcome (/start)
    @bot_func
    def start_command(message):
        reply(message, get_dialog_with_parsing('start', 0, message))

    # Help (/help)
    @bot_func
    def help_command(message):
        dialogue = get_dialog('help')
        for msg in dialogue:
            reply(message, msg)

    # Cancel out of parent command (/cancel)
    @bot_func
    def cancel_command(message):
        reply(message, get_dialog('cancel')[1])

    # Back out of parent command (/back)
    @bot_func
    def back_command(message):
        reply(message, get_dialog('back')[1])

    @bot.callback_query_handler(func=lambda x: True)
    def endwatch_inlines(call):
        if call.message and isinstance(current[call.message.reply_to_message.from_user.id], Endwatch):
            match call.data:
                case '00':
                    reply(call.message.reply_to_message,
                          get_dialog_with_parsing('cancel', 0, call.message.reply_to_message))
                    current[call.message.reply_to_message.from_user.id] = None
                case '10':
                    reply(call.message.reply_to_message,
                          get_dialog_with_parsing('endwatch', 5, call.message.reply_to_message))
                    current[call.message.reply_to_message.from_user.id] = None
                case '01':
                    reply(call.message.reply_to_message,
                          get_dialog_with_parsing('endwatch', 5, call.message.reply_to_message))
                    current[call.message.reply_to_message.from_user.id] = None
                case '11':
                    reply(call.message.reply_to_message,
                          get_dialog_with_parsing('endwatch', 5, call.message.reply_to_message))
                    current[call.message.reply_to_message.from_user.id] = None

    @bot_func
    def showactive_command(message):
        reply(message, get_dialog_with_parsing('showactive', 0, message))
        reply(message, get_dialog_with_parsing('showactive', 1, message))

    @bot_func
    def showinactive_command(message):
        reply(message, get_dialog_with_parsing('showinactive', 0, message))
        reply(message, get_dialog_with_parsing('showinactive', 1, message))

    @bot_func
    def showall_command(message):
        reply(message, get_dialog_with_parsing('showall', 0, message))
        reply(message, get_dialog_with_parsing('showall', 1, message))

    @bot_func
    def search_command(message):
        reply(message, get_dialog_with_parsing('search', 0, message))

    @bot_func
    def status_command(message):
        command, *data = message.text[1:].split()
        if not data:
            reply(message, get_dialog_with_parsing('status', 1, message))
            return
        data = ' '.join(data)
        reply(message, get_dialog_with_parsing('status', 0, message, {'status': data}))
        reply(message, get_dialog_with_parsing('status', 1, message))

    @bot_func
    def allstatuses_command(message):
        reply(message, get_dialog_with_parsing('allstatuses', 0, message))

    @bot_func
    def notifications_command(message):
        reply(message, get_dialog_with_parsing('notifications', 0, message))

    @bot_func
    def stopnotifications_command(message):
        reply(message, get_dialog_with_parsing('stopnotifications', 0, message))

    # Register multi commands
    reg('watch', Watch)
    reg('endwatch', Endwatch)