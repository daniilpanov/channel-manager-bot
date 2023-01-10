from ENV import env
from DB import db
from telethon import TelegramClient, events


class WatchedObject:
    def __init__(self, ch1, h1, ch2, h2):
        self.channel1 = ch1
        self.channel2 = ch2
        self.hashtag1 = h1
        self.hashtag2 = h2


# Добавить проверку на истечение срока
tasks = db.query(
    sql='''SELECT alliances.channel1, alliances.hashtag1, alliances.channel2, alliances.hashtag2 
    FROM tasks JOIN alliances ON alliances.id = tasks.alliance_id 
    WHERE tasks.status IS NULL AND tasks.guilty IS NULL''',
)

all_tasks = []
input_channels = []
input_tags = []

for task in tasks:
    task_obj = WatchedObject(task[0], task[1], task[2], task[3])
    input_channels.append(task_obj.channel1)
    input_tags.append(task_obj.hashtag1)

api_id = env.get('telethon_id')
api_hash = env.get('telethon_hash')
client = TelegramClient('channel_reader', api_id, api_hash)


@client.on(events.NewMessage(chats=input_channels))
async def new_messages_handler(event):
    for tag in input_tags:
        if tag in str(event.message):
            # await client.send_message(OUTPUT_CHANNEL, event.message)
            print("OK")


@client.on(events.MessageDeleted(chats=input_channels))
async def deleted_message_handler(event):
    for tag in input_tags:
        if tag in str(event.message):
            print("deleted")


client.start()
client.run_until_disconnected()
