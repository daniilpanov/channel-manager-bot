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
    WHERE tasks.status IS NULL AND tasks.guilty IS NULL
    AND (
        alliances.days_alive IS NULL
         OR DATE(DATE(alliances.created_at) + alliances.days_alive) >= CURRENT_DATE
    )''',
)

all_tasks = []
input_channels = []
input_tags = []

for task in tasks:
    task_obj = WatchedObject(task[0], task[1], task[2], task[3])

api_id = env.get('telethon_id')
api_hash = env.get('telethon_hash')
with TelegramClient('channel_reader', api_id, api_hash) as client:
    # client.not_connected
    pass

