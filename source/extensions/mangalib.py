from base64 import b64decode
import re
import asyncio
import io
import json

from interactions import (
    Extension,
    extension_command,
    Option,
    CommandContext,
    OptionType,
    Embed,
    EmbedField,
    Button,
    ButtonStyle,
    ComponentContext,
    File,
    extension_component,
    extension_listener,
    Channel,
    Permissions,
    ActionRow,
    Color
)
from interactions.ext.tasks import create_task, IntervalTrigger
from selenium.common.exceptions import NoSuchElementException

from utils.client import MangaLibClient
from utils.mangalib import load_manga_data, check_new_chapter, base64_from_url
from utils.enums import IDS


class MangaLib(Extension):
    def __init__(self, client: MangaLibClient) -> None:
        self.client: MangaLibClient = client
        self.wait_list = []
        self.task_list = []
        self.channel = None
        with open("manga_data.json", encoding="utf-8") as file:
            all_manga_data = json.load(file)
        self.task_list = all_manga_data

    @extension_listener
    async def on_ready(self):
        await asyncio.sleep(5)
        self.check_new_chapters.start(self)

    @create_task(IntervalTrigger(3600))
    async def check_new_chapters(self):
        if self.channel is None:
            await self.get_channel()
        for manga_data in self.task_list:
            try:
                _, chapter_data = check_new_chapter(
                    self.client.webdriver, manga_data["url"]
                )
            except NoSuchElementException as exc:
                print(f"Ошибка с парсингом {manga_data['name']}\n{exc}")
                continue
            if manga_data["last_chapter"]["name"] != chapter_data["name"]:
                manga_data["last_chapter"] = chapter_data
                await self.send_message(manga_data)
                self._write_json()

    async def send_message(self, manga_data: dict):
        file = self._decode_base64(
            base64_from_url(self.client.webdriver, manga_data["image_url"])
        )
        embed = Embed(
            title=manga_data["name"],
            description=f'**{manga_data["last_chapter"]["name"]}**',
            color=Color().blurple,
        )
        embed.set_author("Новая глава!")
        embed.set_thumbnail("attachment://manga.jpg")
        component = Button(
            style=ButtonStyle.LINK,
            label="Читать",
            url=manga_data["last_chapter"]["url"],
        )
        await self.channel.send(embeds=embed, components=component, files=file)

    async def get_channel(self):
        for guild in self.client.guilds:
            if int(guild.id) == IDS.GUILD_ID:
                break
        for channel in guild.channels:
            if isinstance(channel, dict):
                channel = Channel(**channel, _client=self.client._http)
            if int(channel.id) == IDS.CHANNEL_ID:
                self.channel = channel
                break
        else:
            channels = await guild.get_all_channels()
            for channel in channels:
                if int(channel.id) == IDS.CHANNEL_ID:
                    self.channel = channel
                    break
            else:
                print("фикси этот говнокод")

    @extension_command(
        name="mangalib",
        description="Loads data about manga",
        options=[
            Option(
                name="name",
                description="The name of manga",
                type=OptionType.STRING,
                required=True,
            )
        ],
        scope=[829333896561819648, 822119465575383102],
    )
    async def main_command(self, ctx: CommandContext, name: str):
        await ctx.send("Загрузка, подождите...", ephemeral=True)

        manga_data: dict = load_manga_data(self.client.webdriver, name)
        if manga_data is None:
            return await ctx.send("Не найдено!")

        fields = [
            EmbedField(name=k, value=v, inline=True)
            for k, v in manga_data["info"].items()
        ]
        fields.extend(
            [
                EmbedField(name="Жанры", value=", ".join(manga_data["genres"])),
                EmbedField(name="Оценка", value=manga_data["score_info"]["score"]),
                EmbedField(
                    name="Последняя глава", value=manga_data["last_chapter"]["name"]
                ),
            ]
        )
        file = self._decode_base64(
            base64_from_url(self.client.webdriver, manga_data["image_url"])
        )
        embed = Embed(
            title=manga_data["name"],
            description=manga_data["description"],
            fields=fields,
            color=Color().blurple,
        )
        embed.set_thumbnail(url="attachment://manga.jpg")
        components = [
            Button(
                style=ButtonStyle.LINK,
                label="Начать читать",
                url=manga_data["first_chapter_url"],
            ),
            Button(
                style=ButtonStyle.LINK,
                label="Читать последнюю главу",
                url=manga_data["last_chapter"]["url"],
            ),
            Button(
                style=ButtonStyle.SECONDARY,
                label="Подписаться",
                custom_id="subscribe",
            ),
        ]
        for manga in self.task_list:
            if manga["name"] == manga_data["name"]:
                components[-1] = Button(
                    style=ButtonStyle.DANGER,
                    label="Отписаться",
                    custom_id="unsubscribe",
                )
        channel = await ctx.get_channel()
        await channel.send(embeds=embed, components=[components], files=file)

        self.wait_list.append(manga_data)

    @extension_component("subscribe")
    async def mangalib_subscribe(self, ctx: ComponentContext):
        has_perms = await self._check_perms(ctx)
        if not has_perms:
            return

        origin_request = ctx.message.embeds[0].title
        for manga_data in self.wait_list:
            if origin_request == manga_data["name"]:
                self.add_manga_to_task(manga_data)
                break
        else:
            return await ctx.send("oops", ephemeral=True)
        components = self._components_from_json(ctx.message.components)
        components[0].components[-1].disabled = True
        message = ctx.message
        await ctx.send(f"Вы подписались на рассылку `{manga_data['name']}`!")
        await message.edit(components=components, files=[])

    @extension_component("unsubscribe")
    async def mangalib_unsubscribe(self, ctx: ComponentContext):
        has_perms = await self._check_perms(ctx)
        if not has_perms:
            return

        origin_request = ctx.message.embeds[0].title
        for manga_data in self.wait_list:
            if origin_request == manga_data["name"]:
                self.remove_manga_from_task(manga_data)
                break
        else:
            return await ctx.send("oops", ephemeral=True)
        components = self._components_from_json(ctx.message.components)
        components[0].components[-1].disabled = True
        message = ctx.message
        await ctx.send(f"Вы отписались от рассылки на `{manga_data['name']}`!")
        await message.edit(components=components, files=[])

    def add_manga_to_task(self, manga_data: dict):
        self.task_list.append(manga_data)
        self.wait_list.remove(manga_data)
        self._write_json()

    def remove_manga_from_task(self, manga_data: dict):
        self.task_list.remove(manga_data)
        self.wait_list.remove(manga_data)
        self._write_json()

    def _decode_base64(self, base64: str):
        image = io.BytesIO(b64decode(re.sub("data:image/jpeg;base64", "", base64)))
        file = File("manga.jpg", image)
        return file

    def _write_json(self):
        with open("manga_data.json", "w", encoding="utf-8") as file:
            json.dump(self.task_list, file, ensure_ascii=False)

    async def _check_perms(self, ctx: ComponentContext):
        if (
            ctx.author.permissions & Permissions.ADMINISTRATOR.value
            == Permissions.ADMINISTRATOR.value
        ):
            return True
        else:
            await ctx.send(
                "Только Администратор может нажимать на кнопку!", ephemeral=True
            )
            return

    def _components_from_json(self, components_json: dict):
        components = [
            ActionRow(
                components=[
                    Button(**component_json)
                    for component_json in components_json[0]["components"]
                ]
            )
        ]
        return components


def setup(client):
    MangaLib(client)
