from typing import List


class Manga:
    def __init__(self, **kwargs) -> None:
        self.name: str = kwargs[""]
        self.image_url: str = kwargs[""]
        self.info: MangaInfo = kwargs[""]
        self.chapters: List[MangaChapter] = kwargs[""]


class MangaInfo:
    def __init__(self, **kwargs) -> None:
        self.type = kwargs[""]
        self.translation_status = kwargs[""]
        self.publisher = kwargs[""]
        self.year = kwargs[""]
        self.author = kwargs[""]
        self.artist = kwargs[""]
        self.alt_name = kwargs[""]
        self.chapters_count = kwargs[""]
        self.title_status = kwargs[""]


class MangaChapter:
    def __init__(self, **kwargs) -> None:
        self.name: str = kwargs[""]
        self.url: str = kwargs[""]
        self.date: str = kwargs[""]
        self.translator: str = kwargs[""]
