import logging


def init_log(name: str = "app", log_level: str = "INFO") -> None:
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()  # メッセージをコンソールに出力
    handler.setFormatter(logging.Formatter("%(message)s"))  # ログメッセージのフォーマットを設定
    logger.addHandler(handler)  # ロガーがメッセージをハンドラに渡すように設定
    logger.setLevel(log_level)  # ログレベルを設定
