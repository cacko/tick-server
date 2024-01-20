from io import BytesIO
from unittest.mock import Base
from cachable import BinaryStruct
from pydantic import BaseModel
from lametric.models import NowPlayingFrame
from cachable.storage.file import FileStorage
from cachable.storage.filestorage.image import CachableFileImage
from corestring import string_hash
from pixelme import Pixelate
from PIL import Image
from corefile import TempPath
from base64 import b64encode


class NowPlayingImage(CachableFileImage):
    
    def __init__(self, url: str):
        self._url = url
        
    def tocache(self, res: BinaryStruct):
        assert self._path
        tmp = TempPath(self.filename)
        im = Image.open(BytesIO(res.binary))
        im.save(tmp.as_posix())
        pix = Pixelate(tmp, padding=200, block_size=25)
        pix.resize((8, 8))
        pix.image.save(self._path.as_posix())
        

    @property
    def base64(self):
        base64_str = self.path.read_text()
        base64_str = b64encode(base64_str)
        return f"data:image/png;base64,{base64_str.decode()}"
        
    @property
    def filename(self):
        return f"{string_hash(self.url)}.jpg"

    @property
    def url(self):
        return self._url
    

class AndroidNowPlaying(BaseModel):
    artist: str
    art_url: str
    duration: int
    source_id: str
    album: str
    title: str
    
    @property
    def icon(self):
        return NowPlayingImage(self.art_url).base64
    
    @property
    def text(self):
        return f"{self.artist} / {self.title}"
    
    @property
    def index(self):
        return 0
    
    @classmethod
    def from_request(cls, data: dict) -> "AndroidNowPlaying":
        return cls(**{k.split(".")[-1].lower():v for k,v in data.items()})
        
