from os import getenv
#import logging
#logging.basicConfig(level=logging.DEBUG)
from dotenv import load_dotenv
#from interactions.ext import wait_for

from utils.client import MangaLibClient


load_dotenv()

client = MangaLibClient(getenv("BOT_TOKEN"), disable_sync=False)
client.load("extensions.mangalib")
#wait_for.setup(client, True)


@client.event
async def on_ready():
    print("Bot ready!")


client.start()
