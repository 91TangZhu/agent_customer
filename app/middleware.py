"""
中间件模块：全局异常捕获 + 请求耗时记录 + API 限流。
"""
import time
import traceback
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from app.logger import get_logger

api_log = get_logger("api")

# 全局限流器：以客户端 IP 为 key
limiter = Limiter(key_func=get_remote_address)


# ==================== 全局异常捕获 ====================

def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器，捕获未处理异常并返回友好中文报错"""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        api_log.error(
            "未处理异常 %s %s | %s: %s\n%s",
            request.method,
            request.url.path,
            type(exc).__name__,
            str(exc)[:200],
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        api_log.warning("参数校验失败 %s %s: %s", request.method, request.url.path, exc.errors())
        return JSONResponse(
            status_code=422,
            content={
                "detail": "请求参数格式不正确",
                "errors": exc.errors(),
            },
        )


# ==================== 请求耗时记录 ====================

class TimingMiddleware(BaseHTTPMiddleware):
    """记录每个 HTTP 请求的方法、路径、状态码、耗时"""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        api_log.info(
            "%s %s → %s %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


def register_middleware(app: FastAPI):
    """注册所有中间件（异常捕获 + 计时 + 限流）"""
    register_exception_handlers(app)
    app.add_middleware(TimingMiddleware)
    # SlowAPI 限流中间件（必须注册在 TimingMiddleware 之后，否则计时会算上判断耗时）
    app.add_middleware(SlowAPIMiddleware)
