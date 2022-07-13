from os import getenv

from dotenv import load_dotenv

from utils.client import MangaLibClient

# import logging
#
# logging.basicConfig(level=logging.DEBUG)


load_dotenv()

client = MangaLibClient(getenv("BOT_TOKEN"), getenv("MONGO_URL"), disable_sync=False)
client.load("extensions.mangalib")


@client.event
async def on_ready():
    print("Bot ready!")


client.start()
