from DB import db
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
def check_name(name, user_tg_id):
    res = db.query(sql='SELECT * FROM alliances WHERE name=%s AND user_tg_id=%s', params=(name, user_tg_id))
    return not res or len(res) <= 0


class Watch(Command):
    def __init__(self, message):
        super().__init__(message)
        self.reply(message, get_dialog_with_parsing('watch', 0, message))
        self.reply(message, get_dialog_with_parsing('watch', 1, message))
        self.map = [
            self.name_first_id,
            self.first_id_first_hash,
            self.first_hash_second_id,
            self.second_id_second_hash,
            self.second_hash_days,
            self.days_desc,
        ]
        self.state += 1

    def name_first_id(self, message):
        if not check_name(message.text, message.from_user.id):
            reply(message, get_dialog_with_parsing('watch', 9, message))
            return False
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

    def days_desc(self, message):
        if not message.text.isdigit() and message.text.strip() != '-':
            reply(message, get_dialog_with_parsing('watch', 10, message))
            return False
        self.data.append(None)
        self.data.append(None)
        self.data.append(message.text if message.text != '-' else None)
        self.reply(message, get_dialog_with_parsing('watch', 2, message))
        return True

    def finish(self, message):
        self.data[-2] = user_id = message.from_user.id
        self.data[-3] = message.text if message.text != '-' else None
        super().finish(message)
        if db.query(
                sql='''insert into alliances 
                (name, channel1, hashtag1, channel2, hashtag2, description, user_tg_id, days_alive)
                value (%s, %s, %s, %s, %s, %s, %s, %s)''' if self.data[-1]
                else '''insert into alliances
                (name, channel1, hashtag1, channel2, hashtag2, description, user_tg_id)
                value (%s, %s, %s, %s, %s, %s, %s)''',
                params=self.data if self.data[-1] else self.data[0:-1],
        ) is not False:
            alliance_id = db.query(
                sql='SELECT id FROM alliances WHERE name=%s AND user_tg_id=%s',
                params=(self.data[0], user_id)
            )
            if db.query('insert into tasks (alliance_id, user_tg_id) value (%s, %s)',
                        params=(alliance_id[0][0], user_id)) \
                    is not False:
                self.reply(message, get_dialog_with_parsing('watch', 8, message, {'alliance_name': self.data[0]}))
            else:
                db.connection.rollback()
                self.reply(message, get_dialog('__server_error'))
        else:
            self.reply(message, get_dialog('__server_error'))


def check_alliance(alliance, user_id):
    alliance = db.query(
        sql='''SELECT channel1, channel2, alliances.id, status FROM alliances
        JOIN tasks ON (tasks.alliance_id=alliances.id) WHERE name=%s AND alliances.user_tg_id=%s''',
        params=(alliance, user_id),
    )
    return alliance[0] if len(alliance) > 0 else None


class Endwatch(Command):
    def __init__(self, message):
        super().__init__(message)
        self.alliance = None
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

        self.alliance = check_alliance(data, message.from_user.id)
        if not self.alliance:
            reply(message, get_dialog_with_parsing('endwatch', 4, message))
            self.result = True
            return False
        msgtext = get_dialog_with_parsing('endwatch', 0, message) if self.alliance[3] is None \
            else get_dialog_with_parsing('endwatch', 6, message)
        keyboard = types.InlineKeyboardMarkup([
            [types.InlineKeyboardbutton(text=get_dialog_with_parsing('endwatch', 1, message), callback_data='11')],
            [types.InlineKeyboardbutton(text=get_dialog_with_parsing('endwatch', 2, message, {'1': self.alliance[0]}),
                                        callback_data='10')],
            [types.InlineKeyboardbutton(text=get_dialog_with_parsing('endwatch', 2, message, {'1': self.alliance[1]}),
                                        callback_data='01')],
            [types.InlineKeyboardbutton(text=get_dialog_with_parsing('endwatch', 3, message), callback_data='00')],
        ])
        bot.reply_to(message, text=msgtext, reply_markup=keyboard)
        self.state += 1
        return True

    def do_nothing(self):
        pass


def channel(data):
    return data.replace('_', '\\_')


def init():
    # Register simple commands
    # Welcome (/start)
    @bot_func
    def start_command(message):
        user_info = db.query(sql='SELECT id FROM users WHERE identification=%s', params=(message.from_user.id,))
        reply(message, get_dialog_with_parsing('start', int(bool(user_info and len(user_info) > 0)), message))

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
        curr = current[call.message.reply_to_message.from_user.id]
        if call.message and isinstance(curr, Endwatch):
            if call.data == '00':
                reply(call.message.reply_to_message,
                      get_dialog_with_parsing('cancel', 0, call.message.reply_to_message))
                current[call.message.reply_to_message.from_user.id] = None
            elif call.data == '10':
                reply(call.message.reply_to_message,
                      get_dialog_with_parsing('endwatch', 5, call.message.reply_to_message))
                db.query(
                    sql='update tasks set status=FALSE, guilty=FALSE where alliance_id=%s',
                    params=(curr.alliance[2],)
                )
                current[call.message.reply_to_message.from_user.id] = None
            elif call.data == '01':
                reply(call.message.reply_to_message,
                      get_dialog_with_parsing('endwatch', 5, call.message.reply_to_message))
                db.query(
                    sql='update tasks set status=FALSE, guilty=TRUE where alliance_id=%s',
                    params=(curr.alliance[2],)
                )
                current[call.message.reply_to_message.from_user.id] = None
            elif call.data == '11':
                reply(call.message.reply_to_message,
                      get_dialog_with_parsing('endwatch', 5, call.message.reply_to_message))
                db.query(
                    sql='update tasks set status=TRUE, guilty=NULL where alliance_id=%s',
                    params=(curr.alliance[2],)
                )
                current[call.message.reply_to_message.from_user.id] = None

    @bot_func
    def showactive_command(message):
        reply(message, get_dialog_with_parsing('showactive', 0, message))
        alliances = db.query(
            sql='''select alliances.name,
                alliances.channel1, alliances.channel2, alliances.hashtag1, alliances.hashtag2, alliances.days_alive
                from tasks
                join alliances on alliances.id = tasks.alliance_id
                where status is null and tasks.user_tg_id=%s
                and (
                    alliances.days_alive is null
                     or date(date(alliances.created_at) + alliances.days_alive) >= current_date
                ) order by alliances.id desc''',
            params=(message.from_user.id,)
        )
        if alliances and len(alliances) > 0:
            counter = 1
            text = ""
            for i in alliances:
                text += f"{counter}. {channel(i[0])} (@{channel(i[1])}#{channel(i[3])} : @{channel(i[2])}#{channel(i[4])})\n"
                counter += 1
        else:
            text = get_dialog_with_parsing('showactive', 1, message)
        reply(message, text)

    @bot_func
    def showinactive_command(message):
        reply(message, get_dialog_with_parsing('showinactive', 0, message))
        alliances = db.query(
            sql='''
            select alliances.name, alliances.channel1, alliances.channel2, alliances.hashtag1, alliances.hashtag2
            from tasks join alliances on alliances.id = tasks.alliance_id
            where (
                status is not null
                 or alliances.days_alive is not null
                  and date(date(alliances.created_at) + alliances.days_alive) < current_date
            ) and tasks.user_tg_id=%s
            order by alliances.id desc''',
            params=(message.from_user.id,)
        )
        if alliances and len(alliances) > 0:
            counter = 1
            text = ""
            for i in alliances:
                text += f"{counter}. {channel(i[0])} (@{channel(i[1])}#{channel(i[3])} : @{channel(i[2])}#{channel(i[4])})\n"
                counter += 1
        else:
            text = get_dialog_with_parsing('showinactive', 1, message)
        reply(message, text)

    @bot_func
    def showall_command(message):
        reply(message, get_dialog_with_parsing('showall', 0, message))
        alliances = db.query(
            sql='''select alliances.name,alliances.channel1,alliances.channel2,alliances.hashtag1,alliances.hashtag2,
                tasks.status,tasks.guilty,
                (alliances.days_alive is null
                 or date(date(alliances.created_at) + alliances.days_alive) >= current_date
                ) as alive from tasks
                join alliances on alliances.id = tasks.alliance_id where tasks.user_tg_id=%s
                order by alliances.id desc''',
            params=(message.from_user.id,)
        )
        if alliances and len(alliances) > 0:
            counter = 1
            text = ""
            for i in alliances:
                text += f"{counter}. {channel(i[0])} (@{channel(i[1])}#{channel(i[3])} : @{channel(i[2])}#{channel(i[4])}). "
                if i[5] is None:
                    if i[6] == 0:
                        text += "Срок слежки истёк, альянс неактивен"
                    else:
                        text += "Слежка активна"
                elif i[5] or i[5] == 1:
                    text += "Альянс завершён успешно"
                elif i[6] is False or i[6] == 0:
                    text += "Канал @" + i[1] + " нарушил правила. Слежка прекращена"
                elif i[6] is True or i[6] == 1:
                    text += "Канал @" + i[2] + " нарушил правила. Слежка прекращена"
                text += "\n"
                counter += 1
        else:
            text = get_dialog_with_parsing('showall', 1, message)
        reply(message, text)

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
        alliance = db.query(
            sql='''SELECT tasks.status, tasks.guilty, alliances.channel1, alliances.channel2,
                alliances.hashtag1, alliances.hashtag2, 
                (alliances.days_alive is null
                 or date(date(alliances.created_at) + alliances.days_alive) >= current_date
                ) as alive
                FROM tasks JOIN alliances on alliances.id = tasks.alliance_id
                where alliances.name=%s and tasks.user_tg_id=%s''',
            params=(data, message.from_user.id)
        )
        if alliance and len(alliance) > 0:
            a = alliance[0]
            text = f"Альянс {data} (@{channel(a[2])}#{channel(a[4])} : @{channel(a[3])}#{channel(a[5])}): \n"
            if a[0] is None:
                if a[6] == 0:
                    text += "неактивен. Срок слежки истёк"
                else:
                    text += "активен"
            else:
                text += ("завершён " +
                         ("удачно." if a[0] or a[0] == 1
                          else "неудачно (@" + (channel(a[2]) if a[1] is True or a[1] == 1
                                                else channel(a[3]))
                               + " нарушил правила)."))

        else:
            text = get_dialog_with_parsing('status', 1, message)
        reply(message, text)

    @bot_func
    def notifications_command(message):
        db.query(sql='update users set notifications=%s', params=(1,))
        reply(message, get_dialog_with_parsing('notifications', 0, message))

    @bot_func
    def stopnotifications_command(message):
        db.query(sql='update users set notifications=%s', params=(0,))
        reply(message, get_dialog_with_parsing('stopnotifications', 0, message))

    # Register multi commands
    reg('watch', Watch)
    reg('endwatch', Endwatch)
