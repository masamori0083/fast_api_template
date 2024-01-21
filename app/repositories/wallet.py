"""
このファイルは、ウォレットと取引履歴に関連するデータベース操作を非同期で行うためのリポジトリクラスを定義しています。

クラス:
- BaseORM: SQLAlchemyのDeclarativeBaseを継承した基底クラス。全てのORMモデルの基底クラスとして機能します。
- HistoryORM: 取引履歴に関するデータベーステーブルのORMモデル。
- WalletORM: ウォレットに関するデータベーステーブルのORMモデル。
- WalletRepository: ウォレットと取引履歴に関するデータベース操作をカプセル化するリポジトリクラス。

WalletRepositoryクラスは、以下の操作を提供します:
- ウォレットの追加、取得、更新、削除。
- 取引履歴の追加、取得、更新、削除。
- 特定のウォレットに関連する取引履歴の取得。

各メソッドは、非同期で実行され、AsyncSessionを通じてデータベースとの非同期通信を行います。

また、HistoryORMとWalletORMクラスは、それぞれのドメインモデル（History, Wallet）との間でデータを変換するためのメソッドを提供します。
これにより、ビジネスロジック層とデータベース層の間でデータの整合性を保ちつつ、相互に独立した開発が可能になります。
"""


from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    joinedload,
    mapped_column,
    relationship,
    selectinload,
)
from sqlalchemy.sql.expression import select

from app.exceptions import AppException
from app.models import History, HistoryType, Wallet


class BaseORM(DeclarativeBase):
    pass


class HistoryORM(BaseORM):
    """
    ORMでのテーブル定義
    """

    __tablename__ = "histories"
    history_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    amount: Mapped[int] = mapped_column(Integer, CheckConstraint("amount > 0"))
    type: Mapped[HistoryType] = mapped_column(Enum(HistoryType))
    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.wallet_id", ondelete="CASCADE"), index=True
    )
    history_at: Mapped[datetime]
    wallet: Mapped["WalletORM"] = relationship(back_populates="histories")

    @classmethod
    def from_entity(cls, history: History):
        """
        ドメインモデル(エンティティ)からORMモデルに変換する
        """
        return cls(
            history_id=history.history_id,
            name=history.name,
            amount=history.amount,
            type=history.type,
            history_at=history.history_at,
            wallet_id=history.wallet_id,
        )

    def to_entity(self) -> History:
        """
        ORMモデルからドメインモデル(エンティティ)に変換する
        """
        return History.model_validate(self)

    def update(self, history: History) -> None:
        """
        ドメインモデル（エンティティを更新する）
        """
        self.name = history.name
        self.amount = history.amount
        self.type = history.type
        self.wallet_id = history.wallet_id
        self.history_at = history.history_at


class WalletORM(BaseORM):
    __tablename__ = "wallets"
    wallet_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    histories: Mapped[list[HistoryORM]] = relationship(
        back_populates="wallet",
        order_by=HistoryORM.history_at.desc(),
        cascade=("save-update, merge, expunge,delete, delete-orphan"),
    )

    @classmethod
    def from_entity(cls, wallet: Wallet):
        return cls(
            wallet_id=wallet.wallet_id, name=wallet.name, histories=wallet.histories
        )

    def to_entity(self) -> Wallet:
        return Wallet.model_validate(self)

    def update(self, wallet: Wallet, histories: list[HistoryORM]) -> None:
        self.name = wallet.name
        self.histories = histories


class WalletRepository:
    """
    非同期のデータベース操作を行う
    """

    async def add(self, session: AsyncSession, name: str) -> Wallet:
        wallet = WalletORM(name=name, history=[])
        # sessionオブジェクトを作成して、データベースに接続し操作する
        session.add(wallet)  # INSERTが実行される。コミットは行われない
        await session.flush()  # DBに変更を反映する。コミットは行われない
        return wallet.to_entity()

    async def get_by_id(
        self,
        session: AsyncSession,
        wallet_id: int,
    ) -> Wallet | None:
        stmt = (
            select(WalletORM)
            .where(WalletORM.wallet_id == wallet_id)
            .options(
                selectinload(WalletORM.histories)
            )  # 非同期I/Oでは遅延ロードができないので、Eager Loading(selectinload)を使う
        )

        # scalarはクエリの結果として得られる行の集合から最初の列の単一の値を取得する
        wallet = await session.scalar(stmt)
        if not wallet:
            return None
        return wallet.to_entity()

    async def get_all(
        self,
        session: AsyncSession,
    ) -> list[Wallet]:
        stmt = select(WalletORM).options(selectinload(WalletORM.histories))

        # scalarsはクエリの結果として得られる行の集合から最初の列の値を含むリストを取得する
        # ここでは、WalletORMのリストが得られるので、それをWalletエンティティのリストに変換している
        return [wallet.to_entity() for wallet in await session.scalars(stmt)]

    async def add_history(
        self,
        session: AsyncSession,
        wallet_id: int,
        name: str,
        amount: int,
        type_: HistoryType,
        history_at: datetime,
    ) -> History:
        stmt = (
            select(WalletORM)
            .where(WalletORM.wallet_id == wallet_id)
            .options(selectinload(WalletORM.histories))
        )
        wallet = await session.scalar(stmt)
        if not wallet:
            raise AppException()

        history = HistoryORM(
            name=name,
            amount=amount,
            type=type_,
            history_at=history_at,
            wallet_id=wallet.wallet_id,
        )
        wallet.histories.append(history)
        await session.flush()
        return history.to_entity()

    async def update(self, session: AsyncSession, wallet: Wallet) -> Wallet:
        """
        walletを更新する
        """
        stmt = (
            select(WalletORM)
            .where(WalletORM.wallet_id == wallet.wallet_id)
            .options(selectinload(WalletORM.histories))
        )
        wallet_ = await session.scalar(stmt)
        if not wallet_:
            raise AppException()

        wallet_.update(wallet, wallet_.histories)
        await session.flush()
        return wallet_.to_entity()

    async def delete(self, session: AsyncSession, wallet: Wallet) -> None:
        """
        walletを削除する
        """
        stmt = select(WalletORM).where(WalletORM.wallet_id == wallet.wallet_id)
        wallet_ = await session.scalar(stmt)
        if wallet_:
            await session.delete(wallet_)

    async def get_history_by_id(
        self, session: AsyncSession, wallet_id: int, history_id: int
    ) -> History | None:
        stmt = (
            select(HistoryORM)
            .where(
                HistoryORM.wallet_id == wallet_id, HistoryORM.history_id == history_id
            )
            .options(selectinload(HistoryORM.wallet))
        )
        history_ = await session.scalar(stmt)
        if not history_:
            return None

        return history_.to_entity()

    async def update_history(
        self, session: AsyncSession, wallet_id: int, history: History
    ) -> History:
        stmt = select(HistoryORM).where(
            HistoryORM.wallet_id == wallet_id,
            HistoryORM.history_id == history.history_id,
        )
        history_ = await session.scalar(stmt)
        if not history_:
            raise AppException()

        history_.update(history)
        await session.flush()
        return history_.to_entity()

    async def delete_history(
        self, session: AsyncSession, wallet_id: int, history: History
    ) -> None:
        stmt = select(HistoryORM).where(
            HistoryORM.wallet_id == wallet_id,
            HistoryORM.history_id == history.history_id,
        )
        history_ = await session.scalar(stmt)
        if history_:
            await session.delete(history_)
