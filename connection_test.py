from ENV import env
from telethon import TelegramClient, events, sync


api_id = env.get('telethon_id')
api_hash = env.get('telethon_hash')
with TelegramClient('channel_reader', api_id, api_hash) as client:
    @client.on(events.NewMessage(chats=('pubertok',)))
    async def autoanswer(event):
        await client.send_message(event.chat_id, 'You have written: ' + event.message.text)

    client.run_until_disconnected()

