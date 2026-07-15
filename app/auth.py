"""
认证模块：密码哈希 / JWT 签发验证 / FastAPI 依赖注入。
"""
from datetime import datetime, timedelta
from fastapi import Header, HTTPException, Depends
from passlib.context import CryptContext
from jose import jwt, JWTError
from config.settings import settings
from app.logger import get_logger

auth_log = get_logger("auth")

# bcrypt 密码上下文
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== 密码操作 ====================

def hash_password(plain: str) -> str:
    """对明文密码做 bcrypt 哈希"""
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """验证明文密码与哈希是否匹配"""
    return _pwd_ctx.verify(plain, hashed)


# ==================== JWT 操作 ====================

def create_access_token(user_id: int, username: str, is_admin: bool) -> str:
    """签发 JWT 访问令牌"""
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "is_admin": is_admin,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    auth_log.info("JWT 签发: user_id=%d username=%s", user_id, username)
    return token


def decode_access_token(token: str) -> dict | None:
    """验证并解码 JWT，失败返回 None"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return {
            "user_id": int(payload["sub"]),
            "username": payload["username"],
            "is_admin": payload["is_admin"],
        }
    except JWTError:
        return None


# ==================== FastAPI 依赖 ====================

async def get_current_user(authorization: str = Header(..., description="Bearer <token>")) -> dict:
    """从 Authorization 头提取并验证 JWT，返回当前用户信息。未认证返回 401。"""
    if not authorization.startswith("Bearer "):
        auth_log.warning("认证失败: Authorization 头格式错误")
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:]  # 去掉 "Bearer " 前缀
    user = decode_access_token(token)
    if user is None:
        auth_log.warning("认证失败: JWT 无效或已过期")
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user


async def get_optional_user(authorization: str | None = Header(None)) -> dict | None:
    """可选认证：有 token 则返回用户，无则返回 None（不报错）。用于 /chat 向后兼容。"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return decode_access_token(token)


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """要求管理员权限，非管理员返回 403"""
    if not user.get("is_admin"):
        auth_log.warning("权限拒绝: user_id=%s 尝试访问管理员接口", user.get("user_id"))
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    return user
