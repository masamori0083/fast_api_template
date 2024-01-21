"""
ルーティングの定義を行う
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.routes import LoggingRoute

from .histories.views import router as histories_router
from .schemas import (
    GetWalletResponse,
    GetWalletResponseWithHistories,
    GetWalletsResponse,
    PosetwalletRequest,
    PostWalletResponse,
    PutWalletRequest,
    PutWalletResponse,
    Wallet,
)
from .use_case import CreateWallet, DeleteWallet, GetWallet, ListWallets, UpdateWalette

# カスタムルートハンドラを使用する
router = APIRouter(prefix="/v1/wallets", route_class=LoggingRoute)


@router.get("")
async def get_wallets(
    use_case: Annotated[ListWallets, Depends(ListWallets)]
) -> GetWalletsResponse:
    """
    Walletの一覧取得API
    """
    return GetWalletsResponse(
        wallets=[Wallet.model_validate(w) for w in await use_case.execute()]
    )


@router.get(
    "/{wallet_id}",
    response_model=GetWalletResponseWithHistories | GetWalletResponse,
)
async def get_wallet(
    wallet_id: int,
    use_case: Annotated[GetWallet, Depends(GetWallet)],
    include_histories: bool = Query(False, description="収支項目一覧も返すか否か"),
) -> (GetWalletResponseWithHistories | GetWalletResponse):
    """
    Walletの個別取得API
    """
    result = await use_case.execute(wallet_id=wallet_id)
    if include_histories:
        return GetWalletResponseWithHistories.model_validate(result)
    return GetWalletResponse.model_validate(result)


router.include_router(histories_router, prefix="/{wallet_id}")


@router.post("", response_model=PostWalletResponse, status_code=status.HTTP_201_CREATED)
async def post_wallet(
    data: PosetwalletRequest,
    use_case: Annotated[CreateWallet, Depends(CreateWallet)],
) -> PostWalletResponse:
    """
    Walletの作成API
    """
    return PostWalletResponse.model_validate(await use_case.execute(name=data.name))


@router.put("/{wallet_id}", response_model=PutWalletResponse)
async def put_wallet(
    wallet_id: int,
    data: PutWalletRequest,
    use_case: Annotated[UpdateWalette, Depends(UpdateWalette)],
) -> PutWalletResponse:
    """
    Walletの更新API
    """
    return PutWalletResponse.model_validate(
        await use_case.execute(wallet_id=wallet_id, name=data.name)
    )


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wallet(
    wallet_id: int,
    use_case: Annotated[DeleteWallet, Depends(DeleteWallet)],
) -> None:
    """
    Walletの削除API
    """
    await use_case.execute(wallet_id=wallet_id)


# Path: app/api/wallets/histories/views.py
# wallet_idがprefixになるように、historiesのルーティングを定義する
# historiesは各walletに紐づくので、wallet_idを指定する必要がある
router.include_router(histories_router, prefix="/{wallet_id}")
