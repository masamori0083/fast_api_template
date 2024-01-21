import logging

from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)


def init_middlewares(app) -> None:
    @app.middleware("http")  # ミドルウェアの登録(httpリクエストに対するミドルウェア)
    async def log_middleware(request, call_next):
        # httpリクエストにどれだけ時間をかけたかを計測し、ログとして出力するミドルウェア
        st = utcnow()
        # パスオペレーション関数の呼び出し
        response = await call_next(request)
        et = utcnow()
        logger.info("processing time: %f", (et - st).total_seconds())
        return response
