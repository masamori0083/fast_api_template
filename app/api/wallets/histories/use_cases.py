from datetime import datetime

from app.database import AsyncSession, WalletRepository
from app.exceptions import NotFound
from app.models import History, HistoryType
from app.utils.datetime import utcnow

"""
historyのロジックの実装はここに書く
"""


class ListHistories:
    """
    あるwalletn紐づいた取引履歴を全てリスト形式で取得する
    """

    def __init__(self, session: AsyncSession, repo: WalletRepository) -> None:
        self.session = session
        self.repo = repo

    async def execute(self, wallet_id: int) -> list[History]:
        async with self.session() as session:
            wallet = await self.repo.get_by_id(session, wallet_id)
            if not wallet:
                raise NotFound("wallet", wallet_id)

        return wallet.histories


class GetHistory:
    """
    個々の取引履歴を取得する
    """

    def __init__(self, session: AsyncSession, repo: WalletRepository) -> None:
        self.session = session
        self.repo = repo

    async def execute(self, wallet_id: int, history_id: int) -> History:
        async with self.session() as session:
            history = await self.repo.get_history_by_id(session, wallet_id, history_id)
            if not history:
                raise NotFound("history", history_id)

            return history


class CreateHistory:
    """
    取引履歴を作成する
    """

    def __init__(self, session: AsyncSession, repo: WalletRepository) -> None:
        self.session = session
        self.repo = repo

    async def execute(
        self,
        wallet_id: int,
        name: str,
        amount: int,
        type_: HistoryType,
        history_at: datetime,
    ) -> History:
        async with self.session as session:
            wallet = await self.repo.get_by_id(session, wallet_id)
            if not wallet:
                raise NotFound("wallet", wallet_id)

            history = await self.repo.add_history(
                session,
                wallet.wallet_id,
                name=name,
                amount=amount,
                type=type_,
                history_at=history_at,
            )
            return history


class UpdateHistory:
    """
    取引履歴を更新する
    """

    def __init__(
        self,
        session: AsyncSession,
        repo: WalletRepository,
    ) -> None:
        self.session = session
        self.repo = repo

    async def excute(
        self,
        wallet_id: int,
        history_id: int,
        name: str,
        amount: int,
        type_: HistoryType,
        history_at: datetime,
    ) -> History:
        async with self.session as session:
            history = await self.repo.get_history_by_id(session, wallet_id, history_id)
            if not history:
                raise NotFound("history", history_id)

            history.name = name
            history.amount = amount
            history.type = type_
            history.history_at = history_at
            await self.repo.update_history(session, wallet_id, history)
        return history


class DeleteHistory:
    """
    取引履歴を削除する
    """

    def __init__(
        self,
        session: AsyncSession,
        repo: WalletRepository,
    ) -> None:
        self.session = session
        self.repo = repo

    async def excute(
        self,
        wallet_id: int,
        history_id: int,
    ) -> None:
        async with self.session as session:
            history = await self.repo.get_history_by_id(session, wallet_id, history_id)
            if history:
                await self.repo.delete_history(session, history.wallet_id, history)


class MoveHistory:
    """
    指定された取引履歴を指定された別のウォレットに移動する。

    Args:
                wallet_id (int): 移動元のウォレットID
                history_id (int): 移動する取引履歴ID
                destination_id (int): 移動先のウォレットID

    Returns:
                History: 移動した取引履歴

    Raises:
                NotFound: 移動元のウォレットが見つからない場合
    """

    def __init__(self, session: AsyncSession, repo: WalletRepository) -> None:
        self.session = session
        self.repo = repo

    async def execute(
        self,
        wallet_id: int,
        history_id: int,
        destination_id: int,
    ) -> History:
        async with self.session as session:
            # 移動元のウォレットを取得
            history = await self.repo.get_history_by_id(session, wallet_id, history_id)
            if not history:
                raise NotFound("history", history_id)
            # 移動先のウォレットを取得
            wallet = await self.repo.get_by_id(session, destination_id)

            if not wallet:
                raise NotFound("wallet", wallet_id)

            # 移動元のウォレットに移動先のウォレットのIDを設定
            history.wallet_id = wallet.wallet_id
            # 取引履歴が変更されるので、履歴を更新する
            await self.repo.update_history(session, wallet_id, history)
        return history
