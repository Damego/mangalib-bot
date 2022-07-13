from base64 import b64decode
import re
import asyncio
import io

from interactions import (
    option,
    Extension,
    extension_command,
    CommandContext,
    Embed,
    EmbedField,
    Button,
    Component,
    ButtonStyle,
    ComponentContext,
    File,
    extension_component,
    extension_listener,
    Permissions,
    ActionRow,
    Color,
    Channel,
    Snowflake,
    Guild,
    OptionType,
    ChannelType,
    Message,
    LibraryException,
)
from interactions.ext.tasks import create_task, IntervalTrigger
from selenium.common.exceptions import NoSuchElementException

from utils.client import MangaLibClient
from utils.models import *


class MangaLib(Extension):
    def __init__(self, client: MangaLibClient) -> None:
        self.client: MangaLibClient = client
        self.parser = self.client.parser
        self.guilds: list[GuildData] = []
        self.wait_list: dict[int, list[MangaData]] = {}
        self.is_ready = False

    @extension_listener
    async def on_ready(self):
        if self.is_ready:
            return
        await asyncio.sleep(5)

        if not self.guilds:
            self.guilds = await self.client.database.get_guild_datas()
        for guild in self.guilds:
            self.wait_list[int(guild.id)] = []

        self.task_check_new_chapters.start(self)
        self.is_ready = True

    @extension_listener
    async def on_guild_create(self, guild: Guild):
        if not self.guilds:
            self.guilds = await self.client.database.get_guild_datas()
        guild_id = int(guild.id)
        if any(guild_id == guild_data.id for guild_data in self.guilds):
            return
        await self.client.database.add_guild(guild_id)

    @extension_listener
    async def on_guild_remove(self, guild: Guild):
        await self.client.database.remove_guild(int(guild.id))

    @create_task(IntervalTrigger(3600))
    async def task_check_new_chapters(self):
        self.parser.is_busy = True

        for guild in self.guilds:
            try:
                channel = await self.get_channel(guild)
            except LibraryException:
                continue
            if channel is None:
                continue
            for manga_data in guild.manga_list:
                try:
                    chapter_data = self.parser.check_new_chapter(manga_data.url)
                except NoSuchElementException as exc:
                    print(f"Ошибка с парсингом {manga_data.name}\n{exc}")
                    continue
                if manga_data.last_chapter.name != chapter_data.name:
                    manga_data.last_chapter = chapter_data
                    await self.send_message(channel, manga_data)
                    await self.client.database.update_manga(guild.id, manga_data)

        self.parser.is_busy = False

    async def send_message(self, channel: Channel, manga_data: PartialMangaData):
        file = self._decode_base64(self.parser.base64_from_url(manga_data.image_url))
        embed = Embed(
            title=manga_data.name,
            description=f"**{manga_data.last_chapter.name}**",
            color=Color.blurple(),
        )
        embed.set_author("Новая глава!")
        embed.set_thumbnail("attachment://manga.jpg")
        component = Button(
            style=ButtonStyle.LINK,
            label="Читать",
            url=manga_data.last_chapter.url,
        )
        await channel.send(embeds=embed, components=component, files=file)

    async def get_channel(self, guild_data: GuildData):
        if guild_data.channel_id is None:
            return None

        channel = await self.client._http.get_channel(guild_data.channel_id)
        channel = Channel(**channel, _client=self.client._http)
        return channel

    @extension_command(name="mangalib", description="Show information about manga")
    @option(str, name="name", description="The name of manga", required=True)  # type: ignore
    async def main_command(self, ctx: CommandContext, name: str):
        await ctx.send("Загрузка, подождите...", ephemeral=True)
        while self.parser.is_busy:
            pass

        try:
            manga_data: MangaData = self.parser.parse_manga_data(name)
        except Exception:
            return await ctx.send(
                "Произошла ошибка при получении данных. Попробуйте снова или обратитесь к разработчику"
            )

        if manga_data is None:
            return await ctx.send("Не найдено!")
        fields = [
            EmbedField(name=k, value=v, inline=True) for k, v in manga_data.info.items()
        ]
        fields.extend(
            [
                EmbedField(name="Жанры", value=", ".join(manga_data.genres)),
                EmbedField(name="Оценка", value=manga_data.score.score),
                EmbedField(name="Последняя глава", value=manga_data.last_chapter.name),
            ]
        )
        file = self._decode_base64(self.parser.base64_from_url(manga_data.image_url))
        embed = Embed(
            title=manga_data.name,
            description=manga_data.description,
            fields=fields,
            color=Color.blurple(),
        )
        embed.set_thumbnail(url="attachment://manga.jpg")
        old_manga = self.get_manga(ctx.guild_id, manga_data.name)
        components = self._render_components(
            manga_data, True if old_manga is None else False
        )
        channel = await ctx.get_channel()
        await channel.send(embeds=embed, components=[components], files=file)  # type: ignore
        self.wait_list[int(ctx.guild_id)].append(manga_data)

    @extension_component("subscribe")
    async def mangalib_subscribe(self, ctx: ComponentContext):
        message, components, manga_data = await self.base_sub_unsub_logic(ctx)
        if message is None:
            return

        await self.add_manga_to_task(int(ctx.guild_id), manga_data)
        await ctx.send(f"Вы подписались на рассылку `{manga_data.name}`!")
        await message.edit(components=components, files=[])

    @extension_component("unsubscribe")
    async def mangalib_unsubscribe(self, ctx: ComponentContext):
        message, components, manga_data = await self.base_sub_unsub_logic(ctx)
        if message is None:
            return

        await self.remove_manga_from_task(int(ctx.guild_id), manga_data)
        await ctx.send(f"Вы отписались от рассылки на `{manga_data.name}`!")
        await message.edit(components=components, files=[])

    async def base_sub_unsub_logic(self, ctx: ComponentContext):
        has_perms = self._check_perms(ctx)
        if not has_perms:
            await ctx.send(
                "Только Администратор сервера может подписываться/отписываться!",
                ephemeral=True,
            )
            return None, None, None

        manga_name = ctx.message.embeds[0].title
        manga_data = self.get_manga(ctx.guild_id, manga_name)
        if manga_data is None:
            await ctx.send("Каким-то образом не найдено", ephemeral=True)
            return None, None, None

        components = self._components_from_json(ctx.message.components)  # type: ignore
        components[0].components[-1].disabled = True
        message = ctx.message

        return message, components, manga_data

    def get_manga(
        self, guild_id: int | Snowflake, name: str
    ) -> PartialMangaData | MangaData | None:
        wait_manga = self.wait_list.get(int(guild_id))
        if wait_manga is None:
            return None
        for manga_data in wait_manga:
            if manga_data.name == name:
                wait_manga.remove(manga_data)
                return manga_data

        guild_data = self.get_guild_data(guild_id)
        if guild_data is None:
            return

        for manga_data in guild_data.manga_list:
            if name == manga_data.name:
                return manga_data

    def get_guild_data(self, guild_id: int | Snowflake) -> GuildData:
        for guild in self.guilds:
            if guild.id == (guild_id if isinstance(guild_id, int) else int(guild_id)):
                return guild

    def _render_components(self, manga_data: MangaData, is_subscribe: bool):
        return [
            Button(
                style=ButtonStyle.LINK,
                label="Начать читать",
                url=manga_data.first_chapter.url,
            ),
            Button(
                style=ButtonStyle.LINK,
                label="Читать последнюю главу",
                url=manga_data.last_chapter.url,
            ),
            Button(
                style=ButtonStyle.SECONDARY,
                label="Подписаться",
                custom_id="subscribe",
            )
            if is_subscribe
            else Button(
                style=ButtonStyle.DANGER,
                label="Отписаться",
                custom_id="unsubscribe",
            ),
        ]

    async def add_manga_to_task(self, guild_id: int, manga_data: MangaData):
        partial_manga_data = manga_data.to_partial()
        for guild in self.guilds:
            if guild.id == guild_id:
                guild.manga_list.append(partial_manga_data)
                break
        await self.client.database.add_manga(guild_id, partial_manga_data)

    async def remove_manga_from_task(self, guild_id: int, manga_data: MangaData):
        partial_manga_data = manga_data.to_partial()
        for guild in self.guilds:
            if guild.id == guild_id:
                guild.manga_list.remove(partial_manga_data)
                break
        await self.client.database.remove_manga(guild_id, partial_manga_data)

    def _decode_base64(self, base64: str):
        image = io.BytesIO(b64decode(re.sub("data:image/jpeg;base64", "", base64)))
        return File("manga.jpg", image)

    def _check_perms(self, ctx: ComponentContext):
        return (
            ctx.author.permissions & Permissions.ADMINISTRATOR.value
            == Permissions.ADMINISTRATOR.value
        )

    def _components_from_json(self, components_json: dict) -> list[ActionRow]:
        return [
            ActionRow(
                components=[
                    Component(**component_json)
                    for component_json in action_row["components"]
                ]
            )
            for action_row in components_json
        ]

    @extension_command(name="set-channel", description="Set channel for notifications")
    @option(
        OptionType.CHANNEL,
        name="channel",
        description="The channel for notifications",
        channel_types=[ChannelType.GUILD_TEXT],
        required=True,
    )
    async def test(self, ctx: CommandContext, channel: Channel):
        try:
            message = await channel.send(
                "Проверка доступа к каналу. Сообщение удалится через 5 секунд."
            )
        except LibraryException:
            return await ctx.send(f"Нет доступа к каналу {channel.mention}")

        async def remove_message(message: Message):
            await asyncio.sleep(5)
            await message.delete()

        loop = asyncio.get_event_loop()
        loop.create_task(remove_message(message))

        await self.client.database.set_channel(int(ctx.guild_id), int(channel.id))
        await ctx.send("Канал для уведомлений установлен!")


def setup(client):
    MangaLib(client)
