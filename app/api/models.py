from io import BytesIO
import logging
from pathlib import Path
from typing import Optional
from cachable import BinaryStruct
from pydantic import BaseModel
from app.lametric.models import NowPlayingFrame
from cachable.storage.file import FileStorage
from cachable.storage.filestorage.image import CachableFileImage
from corestring import string_hash
from pixelme import Pixelate
from PIL import Image
from corefile import TempPath
from base64 import b64encode
from uuid import uuid4
import requests
import shutil


def download_image(url: str) -> TempPath:
    tmp_file = TempPath(f"{uuid4()}.jpg")
    response = requests.get(url, stream=True)
    with tmp_file.open("wb") as out_file:
        shutil.copyfileobj(response.raw, out_file)
    return tmp_file


class NowPlayingImage(CachableFileImage):
    def __init__(self, url: str):
        self._url = url
        super().__init__()

    def tocache(self, image_path: Path):
        assert self._path
        pix = Pixelate(image_path, padding=200, block_size=25, result_path=self._path)
        pix.resize((8, 8))
        self._path = pix.image_path

    @property
    def storage(self):
        return FileStorage

    @property
    def base64(self):
        logging.info(self._path)
        base64_str = self.path.read_bytes()
        base64_str = b64encode(base64_str)
        return f"data:image/png;base64,{base64_str.decode()}"

    @property
    def filename(self):
        return f"{string_hash(self.url)}.png"

    @property
    def url(self):
        return self._url

    def _init(self):
        if self.isCached:
            return
        try:
            self.tocache(download_image(self.url))
        except Exception as e:
            logging.exception(e)
            self._path = self.DEFAULT


class AndroidNowPlaying(BaseModel):
    artist: str
    duration: int
    album: str
    title: str
    art_uri: Optional[str] = None
    display_icon_uri: Optional[str] = None
    DEFAULT = "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAAXNSR0IArs4c6QAAAIRlWElmTU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAAUAAAABAAAAUgEoAAMAAAABAAIAAIdpAAQAAAABAAAAWgAAAAAAAABIAAAAAQAAAEgAAAABAAOgAQADAAAAAQABAACgAgAEAAAAAQAAAAigAwAEAAAAAQAAAAgAAAAAZr4WUQAAAAlwSFlzAAALEwAACxMBAJqcGAAAAVlpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDYuMC4wIj4KICAgPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICAgICAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgICAgICAgICAgeG1sbnM6dGlmZj0iaHR0cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iPgogICAgICAgICA8dGlmZjpPcmllbnRhdGlvbj4xPC90aWZmOk9yaWVudGF0aW9uPgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KGV7hBwAAAMNJREFUGBk1jz0ORUAUhc88o8ACtCqJRqWxCb3EIqxLZQlWYAMiQkShUBA/lfPeneTd8pt7z/lGLctC27Yhc10XjuNA3/fwfR9BEADruvI8T9Z1zSiK6Lguf7usqor7vlO/7wuSGIYBYRiiLEt0XQfLsiBvWikl6XAcB1mWmaU/E67lWoB4JEmCOI6htcY4joZ/JOq+b3GB53lo2xZpmpoDScA8z8zz3IiJcNM0LIqCPw9u20Y1TZNA8y2pkJFKqX6eB1/vWGbiI93EewAAAABJRU5ErkJggg=="

    @property
    def icon(self):
        try:
            assert self.art_uri
            return NowPlayingImage(self.art_uri).base64
        except AssertionError:
            pass
        try:
            assert self.display_icon_uri
            return NowPlayingImage(self.display_icon_uri).base64
        except:
            pass
        return self.DEFAULT

    @property
    def text(self):
        return f"{self.artist} / {self.title}"

    @property
    def index(self):
        return 0

    @classmethod
    def from_request(cls, data: dict) -> "AndroidNowPlaying":
        return cls(**{k.split(".")[-1].lower(): v for k, v in data.items()})

    def get_frame(self) -> NowPlayingFrame:
        return NowPlayingFrame(
            text=self.text, icon=self.icon, duration=self.duration // 1000
        )
