from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\nHere is your session string:\n")
    print(client.session.save())
    print("\nStore this string in your config.py file as SESSION_STRING\n")
