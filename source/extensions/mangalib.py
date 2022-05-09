import asyncio
from base64 import b64decode
import re
import io

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
    ActionRow,
    ComponentContext,
    File
)

from utils.client import MangaLibClient
from utils.mangalib import load_manga_data
from utils.enums import DiscordColors


class MangaLib(Extension):
    def __init__(self, bot: MangaLibClient) -> None:
        self.bot = bot

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

        manga_data: dict = load_manga_data(self.bot.webdriver, name)
        if manga_data is None:
            return await ctx.send("Не найдено!")

        fields = [
            EmbedField(name=k, value=v, inline=True)
            for k, v in manga_data["info"].items()
        ]
        fields.extend([
            EmbedField(name="Жанры", value=", ".join(manga_data["genres"])),
            EmbedField(name="Оценка", value=manga_data["score_info"]["score"]),
            EmbedField(name="Последняя глава", value=manga_data["last_chapter"]["name"]),
        ])

        image = io.BytesIO(b64decode(re.sub("data:image/jpeg;base64", '', manga_data["image_base64"])))
        file = File("aboba.jpg", image)
        embed = Embed(
            title=manga_data["name"],
            description=manga_data["description"],
            fields=fields,
            color=DiscordColors.BLURPLE,
        )
        embed.set_thumbnail(url="attachment://aboba.jpg")
        # TODO Проверить, есть ли манга в json, если да, то кнопка `отписаться`
        components = ActionRow(
            components=[
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
        )
        channel = await ctx.get_channel()
        await channel.send(embeds=embed, components=[components], files=file)

        return
        try:
            button_ctx: ComponentContext = await self.bot.wait_for_component(
                components=components, timeout=60
            )
        except asyncio.TimeoutError:
            components = ActionRow(
                components=[
                    Button(
                        style=ButtonStyle.LINK,
                        label="Читать последнюю главу",
                        url=manga_data["last_chapter"]["url"],
                    ),
                    Button(
                        style=ButtonStyle.SECONDARY,
                        label="Подписаться",
                        custom_id="subscribe",
                        disabled=True,
                    ),
                ]
            )
            await message.edit(components=components)
            return

        # TODO Записать в json новую мангу
        await button_ctx.send("ok", ephemeral=True)


def setup(client):
    MangaLib(client)
