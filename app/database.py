import logging
from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy import Connection, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.exceptions import AppException
from app.repositories import BaseORM
from app.repositories import WalletRepository as _WalletRepository

logger = logging.getLogger(__name__)
async_engine = create_async_engine("sqlite+aiosqlite:///database.db")

# 非同期データベースセッションを作成する
AsyncSessionLocal = async_sessionmaker(bind=async_engine, autoflush=False)


async def get_session() -> AsyncIterator[async_sessionmaker]:
    """
    非同期データベースセッションを取得する
    """
    try:
        yield AsyncSessionLocal
    except SQLAlchemyError as e:
        logger.exception(e)  # ログにエラーを出力する
        raise AppException() from e


AsyncSession = Annotated[async_sessionmaker, Depends(get_session)]

WalletRepository = Annotated[_WalletRepository, Depends(_WalletRepository)]


async def create_database_if_not_exist() -> None:
    """
    起動時にテーブルが存在しない場合は作成する
    """

    def create_table_if_not_exist(sync_conn: Connection) -> None:
        """
        テーブルが存在しない場合は作成する
        """
        if not inspect(sync_conn.engine).has_table("wallets"):
            BaseORM.metadata.create_all(sync_conn.engine)

    async with async_engine.connect() as conn:
        # run_sync()で同期処理を実行する。この時にsync_connが渡される
        await conn.run_sync(create_table_if_not_exist)
