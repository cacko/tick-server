from dataclasses import dataclass
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
from enum import Enum


class RPCMethod(Enum):
    RECEIVE = "receive"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GroupInfo:
    groupId: str
    type: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Attachment:
    contentType: str
    filename: str
    id: str
    size: int


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SentMessage:
    destination: Optional[str]
    destinationNumber: Optional[str]
    destinationUuid: Optional[str]
    timestamp: Optional[int]
    message: Optional[str]
    groupInfo: Optional[GroupInfo] = None
    attachments: Optional[list[Attachment]] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SyncMessage:
    sentMessage: Optional[SentMessage] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ReceiptMessage:
    when: int
    isDelivery: bool
    isRead: bool
    isViewed: bool


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DataMessage:
    timestamp: Optional[int]
    message: Optional[str]
    groupInfo: Optional[GroupInfo] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MessageEnvelope:
    source: str
    sourceName: str
    timestamp: int
    syncMessage: Optional[SyncMessage] = None
    receiptMessage: Optional[ReceiptMessage] = None
    dataMessage: Optional[DataMessage] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MessageParams:
    account: str
    envelope: MessageEnvelope


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Message:
    jsonrpc: float
    method: Optional[str] = None
    params: Optional[MessageParams] = None

    @property
    def group(self) -> str:
        try:
            envelope = self.params.envelope
            if envelope.syncMessage is not None:
                return envelope.syncMessage.sentMessage.groupInfo.groupId
            if envelope.dataMessage is not None:
                return envelope.dataMessage.groupInfo.groupId
        except Exception:
            return None

    @property
    def source(self) -> str:
        try:
            return self.params.envelope.source
        except Exception:
            return None

    @property
    def message(self) -> str:
        try:
            envelope = self.params.envelope
            if envelope.syncMessage is not None:
                return envelope.syncMessage.sentMessage.message
            if envelope.dataMessage is not None:
                return envelope.dataMessage.message
        except Exception:
            return None

    @property
    def attachment(self) -> Attachment:
        try:
            envelope = self.params.envelope
            if all([
                envelope.syncMessage is not None,
                envelope.syncMessage.sentMessage.attachments is not None
            ]):
                return envelope.syncMessage.sentMessage.attachments[0]
            if envelope.dataMessage is not None:
                pass
        except Exception:
            return None
