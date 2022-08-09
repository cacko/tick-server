import logging
from .base import BaseWidget, WidgetMeta
from datetime import datetime, timezone
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config, Undefined
from marshmallow import fields
from typing import Optional
import re
from enum import Enum
import requests
from app.config import Config

TEAM_ID = 131


class EventStatus(Enum):
    HT = "HT"
    FT = "FT"
    PPD = "PPD"
    CNL = "CNL"
    AET = "AET"
    NS = "NS"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GameCompetitor:
    id: Optional[int] = None
    countryId: Optional[int] = None
    sportId: Optional[int] = None
    name: Optional[str] = None
    score: Optional[int] = None
    isQualified: Optional[bool] = None
    toQualify: Optional[bool] = None
    isWinner: Optional[bool] = None
    type: Optional[int] = None
    imageVersion: Optional[int] = None
    mainCompetitionId: Optional[int] = None
    redCards: Optional[int] = None
    popularityRank: Optional[int] = None
    symbolicName: Optional[str] = None

    @property
    def flag(self) -> str:
        pass

    @property
    def shortName(self) -> str:
        if self.symbolicName:
            return self.symbolicName
        parts = self.name.split(' ')
        if len(parts) == 1:
            return self.name[:3].upper()
        return f"{parts[0][:1]}{parts[1][:2]}".upper()


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Game:
    id: int
    sportId: int
    competitionId: int
    competitionDisplayName: str
    startTime: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    statusGroup: int
    statusText: str
    shortStatusText: str
    gameTimeAndStatusDisplayType: int
    gameTime: int
    gameTimeDisplay: str
    homeCompetitor: GameCompetitor
    awayCompetitor: GameCompetitor
    seasonNum: Optional[int] = 0
    stageNum: Optional[int] = 0
    justEnded: Optional[bool] = None
    hasLineups: Optional[bool] = None
    hasMissingPlayers: Optional[bool] = None
    hasFieldPositions: Optional[bool] = None
    hasTVNetworks: Optional[bool] = None
    hasBetsTeaser: Optional[bool] = None
    winDescription: Optional[str] = ""
    aggregateText: Optional[str] = ""

    @property
    def postponed(self) -> bool:
        try:
            status = EventStatus(self.shortStatusText)
            return status == EventStatus.PPD
        except ValueError:
            return False

    @property
    def canceled(self) -> bool:
        try:
            status = EventStatus(self.shortStatusText)
            return status == EventStatus.CNL
        except ValueError:
            return False

    @property
    def not_started(self) -> bool:
        res = self.startTime > datetime.now(tz=timezone.utc)
        return res

    @property
    def ended(self) -> bool:
        if self.not_started:
            return False

        status = self.shortStatusText

        try:
            _status = EventStatus(status)
            if _status in (EventStatus.FT, EventStatus.AET, EventStatus.PPD):
                return True
            return _status == EventStatus.HT or re.match(r"^\d+$", status)
        except ValueError:
            return False


class RMWidget(BaseWidget, metaclass=WidgetMeta):

    def __init__(self, widget_id: str, widget):
        super().__init__(widget_id, widget)
        self.get_schedule()

    def onShow(self):
        pass

    def onHide(self):
        pass

    def get_schedule(self):
        url = f"{Config.znayko.host}/team_schedule/{TEAM_ID}"
        res = requests.get(url)
        data = res.json()
        schedule = Game.schema().load(data, many=True)
