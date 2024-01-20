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
        pix = Pixelate(image_path, padding=200, block_size=25)
        pix.resize((8, 8))
        pix.image.save(self._path.as_posix())
        

    @property
    def storage(self):
        return FileStorage

    @property
    def base64(self):
        logging.info(self._path)
        base64_str = self.path.read_text()
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
    
    @property
    def icon(self):
        return NowPlayingImage(self.art_uri).base64
    
    @property
    def text(self):
        return f"{self.artist} / {self.title}"
    
    @property
    def index(self):
        return 0
    
    @classmethod
    def from_request(cls, data: dict) -> "AndroidNowPlaying":
        return cls(**{k.split(".")[-1].lower():v for k,v in data.items()})
        
    
    def get_frame(self) -> NowPlayingFrame:
        return NowPlayingFrame(
            text=self.text,
            icon=self.icon,
            duration=self.duration//1000
        )
