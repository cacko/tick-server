from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from typing import Optional


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class NotificationFrame:
    text: str
    icon: str
    index: Optional[int] = 0


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class NotificationModel:
    frames: list[NotificationFrame]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Notification:
    model: NotificationModel
    priority: str = "info"
    icon_type: str = "none"
