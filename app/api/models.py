from unittest.mock import Base
from pydantic import BaseModel
from lametric.models import NowPlayingFrame


class AndroidNowPlaying(BaseModel):
    artist: str
    art_url: str
    duration: int
    source_id: str
    album: str
    title: str
    
    @property
    def icon(self):
        return ""
    
    @property
    def contentFrame(self):
        return NowPlayingFrame(
            text=f"{self.artist} / {self.title}",
            duration=int(self.duration / 1000),
            icon=self.icon
        )
    
    @classmethod
    def from_request(cls, data: dict) -> "AndroidNowPlaying":
        return cls(**{k.split(".")[-1].lower():v for k,v in data.items()})
        
