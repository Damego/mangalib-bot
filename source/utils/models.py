from attrs import define, field
from typing import List


__all__ = ["GuildData", "ScoreData", "Chapter", "MangaData", "PartialMangaData"]


def convert_list(obj):
    def wrapper(data_list: list):
        return [obj(**data) for data in data_list]

    return wrapper


def convert(obj):
    def wrapper(data):
        return data if isinstance(data, obj) else obj(**data)

    return wrapper


@define
class ScoreData:
    score: str
    count: str


@define
class Chapter:
    name: str
    url: str


@define
class MangaData:
    name: str
    description: str
    image_url: str
    info: dict
    genres: List[str]
    url: str
    score: ScoreData = field(converter=convert(ScoreData))
    first_chapter: Chapter = field(converter=convert(Chapter))
    last_chapter: Chapter = field(converter=convert(Chapter))

    def to_partial(self):
        return PartialMangaData(
            name=self.name,
            url=self.url,
            image_url=self.image_url,
            last_chapter=self.last_chapter,
        )


@define
class PartialMangaData:
    name: str
    url: str
    image_url: str
    last_chapter: Chapter = field(converter=convert(Chapter))


@define
class GuildData:
    id: int
    channel_id: int
    manga_list: list[PartialMangaData] = field(converter=convert_list(PartialMangaData))
