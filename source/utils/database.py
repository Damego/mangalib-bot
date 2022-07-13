import ssl

from attrs import asdict
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from .models import MangaData, GuildData


class DataBaseClient:
    def __init__(self, token: str):
        self._client: MongoClient | AsyncIOMotorClient = AsyncIOMotorClient(
            token, ssl_cert_reqs=ssl.CERT_NONE
        )
        self.collection = self._client["MANGALIB_BOT"]["GUILDS"]

    async def add_guild(self, guild_id: int):
        await self.collection.insert_one(
            {"_id": guild_id, "manga_list": [], "channel_id": None}
        )

    async def remove_guild(self, guild_id: int):
        await self.collection.delete_one({"_id": guild_id})

    async def get_guild_datas(self) -> list[GuildData]:
        guilds_cursor = self.collection.find()
        guilds = []
        async for guild_data in guilds_cursor:
            guild_data["id"] = guild_data.pop("_id")
            guilds.append(GuildData(**guild_data))
        return guilds

    async def add_manga(self, guild_id: int, manga_data: MangaData):
        await self.collection.update_one(
            {"_id": guild_id},
            {"$push": {"manga_list": asdict(manga_data)}},
            upsert=True,
        )

    async def update_manga(self, guild_id: int, manga_data: MangaData):
        await self.collection.update_one(
            {"_id": guild_id, "manga_list.name": manga_data.name},
            {
                "$set": {f"manga_list.$.{key}": value}
                for key, value in asdict(manga_data).items()
            },
            upsert=True,
        )

    async def remove_manga(self, guild_id: int, manga_data: MangaData):
        await self.collection.update_one(
            {"_id": guild_id},
            {"$pull": {"manga_list": asdict(manga_data)}},
            upsert=True,
        )

    async def set_channel(self, guild_id: int, channel_id: int):
        await self.collection.update_one(
            {"_id": guild_id}, {"$set": {"channel_id": channel_id}}
        )
