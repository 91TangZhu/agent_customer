"""
结构化日志模块：提供统一日志记录能力，覆盖 API 耗时、RAG 检索、LLM 调用、认证事件。
所有模块通过 logger(name) 获取对应 logger 实例。
"""
import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
_LOGGERS: dict[str, logging.Logger] = {}
_INITIALIZED = False


def _init():
    """初始化日志系统（只执行一次）"""
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    os.makedirs(_LOG_DIR, exist_ok=True)

    # 根 logger 设置
    root = logging.getLogger("agent_customer")
    root.setLevel(logging.DEBUG)

    # 格式：2026-07-15 10:30:00 | INFO     | api       | GET /health 200 2ms
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-10s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出 (INFO+)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 文件输出 (DEBUG+, 轮转: 10MB × 5)
    file_handler = RotatingFileHandler(
        os.path.join(_LOG_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger（自动注册到 agent_customer 命名空间）"""
    _init()
    if name not in _LOGGERS:
        _LOGGERS[name] = logging.getLogger(f"agent_customer.{name}")
    return _LOGGERS[name]
