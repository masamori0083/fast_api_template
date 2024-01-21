from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, Field, PositiveInt, WrapSerializer

from app.utils.datetime import to_utc

UTCDatetime = Annotated[datetime, WrapSerializer(to_utc)]


class BaseModel(_BaseModel):
    # フィールドと同名の属性を持つオブジェクトから
    # モデルの生成を可能にする
    model_config = ConfigDict(from_attribute=True)


class HistoryType(StrEnum):
    INCOME = "INCOME"
    OUTCOME = "OUTCOME"


class History(BaseModel):
    history_id: int
    name: str
    amount: PositiveInt
    type: HistoryType
    history_at: UTCDatetime
    wallet_id: int


class Wallet(BaseModel):
    wallet_id: int
    name: str
    histories: list[History]

    @property
    def balance(self) -> int:
        return sum(
            h.amount if h.type == HistoryType.INCOME else -h.amount
            for h in self.histories
        )
