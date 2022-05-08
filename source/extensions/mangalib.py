import asyncio
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
        scope=829333896561819648,
    )
    async def main_command(self, ctx: CommandContext, name: str):
        await ctx.defer()

        manga_data: dict = load_manga_data(self.bot.webdriver, name)
        if manga_data is None:
            return await ctx.send("Не найдено!")

        fields = [
            EmbedField(name=k, value=v, inline=True)
            for k, v in manga_data["manga_info"].items()
        ]
        fields.append(
            EmbedField(name="Последняя глава", value=manga_data["last_chapter"]["name"])
        )

        embed = Embed(
            title=manga_data["name"],
            fields=fields,
            color=DiscordColors.BLURPLE,
        )
        embed.set_image(url=manga_data["image_url"])
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

        message = await ctx.send(embeds=embed, components=[components])

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
        await button_ctx.send("Вы успешно подписались на уведомления!", ephemeral=True)


def setup(client):
    MangaLib(client)
