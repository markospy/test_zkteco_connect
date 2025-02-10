import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Device(SQLModel, table=True):
    ID: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    DevSN: str | None = Field(default=None, max_length=50, index=True)
    DevName: str | None = Field(default=None, max_length=50)
    ATTLOGStamp: str | None = Field(default=None, max_length=50)
    OPERLOGStamp: str | None = Field(default=None, max_length=50)
    ATTPHOTOStamp: str | None = Field(default=None, max_length=50)
    ErrorDelay: str | None = Field(default=60, max_length=50)
    TransFlag: str | None = Field(default=None, max_length=100)
    Realtime: str | None = Field(default=1, max_length=1)
    TransInterval: str | None = Field(default=None, max_length=10)
    TransTimes: str | None = Field(default=None, max_length=60)
    Encrypt: str | None = Field(default=0, max_length=1)
    LastRequestTime: datetime | None
    DevIP: str | None = Field(default=None, max_length=50)
    UserCount: int | None = Field(default=0)
    AttCount: int | None = Field(default=0)
    FpCount: int | None = Field(default=0)
    TimeZone: str | None = Field(default="-05:00", max_length=50)
    Timeout: int | None = Field(default=60)
    SyncTime: int | None = Field(default=3600)
