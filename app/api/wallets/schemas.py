"""
エンドポイントのリクエスト・レスポンスのスキーマを定義するモジュール.
Pydanticの機能を使用するため、PydanticのBaseModelを継承している.
Pydanticによって、バリデーションやシリアル、デシリアルが行われる.
"""

from pydantic import Field

from app.models import BaseModel

from .histories.schemas import History


class Wallet(BaseModel):
    wallet_id: int
    name: str
    balance: int = Field(..., description="現時点での予算")  # "..."はこのフィールドが必須項目であることを示す


class GetWalletsResponse(BaseModel):
    wallets: list[Wallet]


class GetWalletResponse(Wallet):
    pass


class GetWalletResponseWithHistories(Wallet):
    histories: list[History] = Field(..., description="関連する収支項目一覧")


class PosetwalletRequest(BaseModel):
    name: str


class PostWalletResponse(Wallet):
    pass


class PutWalletRequest(BaseModel):
    name: str


class PutWalletResponse(Wallet):
    pass
