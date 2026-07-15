"""
SQLite 数据库连接与基础查询封装。
所有 SQL 操作都走这个模块，方便后续切换数据库。
"""
import sqlite3
import os
from config.settings import settings


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（自动创建 data 目录）"""
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果支持字典式访问 row["name"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==================== 用户查询（原有）====================

def query_user_by_phone(phone: str) -> dict | None:
    """根据手机号查询用户"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()
    conn.close()
    return dict(row) if row else None


def query_user_by_id(user_id: int) -> dict | None:
    """根据用户ID查询用户"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ==================== 订单查询（原有）====================

def query_orders_by_user_id(user_id: int) -> list[dict]:
    """根据用户ID查所有订单"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_order_by_no(order_no: str) -> dict | None:
    """根据订单号精确查询"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ==================== 物流查询（原有）====================

def query_logistics_by_order_id(order_id: int) -> dict | None:
    """根据订单ID查物流信息"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM logistics WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ==================== 认证用户管理（新增）====================

def create_auth_user(username: str, password_hash: str, is_admin: int = 0) -> int:
    """创建认证用户，返回新用户 ID"""
    from datetime import datetime
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO auth_users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
        (username, password_hash, is_admin, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_auth_user_by_username(username: str) -> dict | None:
    """根据用户名查询认证用户"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM auth_users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_auth_user_by_id(user_id: int) -> dict | None:
    """根据用户 ID 查询认证用户"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM auth_users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_password(user_id: int, new_hash: str) -> None:
    """更新用户密码哈希"""
    conn = get_connection()
    conn.execute("UPDATE auth_users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()


# ==================== 知识库文档管理（新增）====================

def create_document(title: str, content: str, category: str) -> int:
    """创建知识库文档，返回文档 ID"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO documents (title, content, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (title, content, category, now, now),
    )
    doc_id = cur.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def get_document_by_id(doc_id: int) -> dict | None:
    """根据 ID 查询文档"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_document(doc_id: int, title: str | None, content: str | None, category: str | None) -> bool:
    """更新文档（只更新非 None 字段），返回是否成功"""
    from datetime import datetime
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if content is not None:
        fields.append("content = ?")
        values.append(content)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
    if not fields:
        return False
    fields.append("updated_at = ?")
    values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    values.append(doc_id)
    conn = get_connection()
    conn.execute(f"UPDATE documents SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_document(doc_id: int) -> bool:
    """删除文档，返回是否成功"""
    conn = get_connection()
    cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def list_documents(category: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
    """分页查询文档列表，返回 (items, total)"""
    conn = get_connection()
    if category:
        total = conn.execute("SELECT COUNT(*) FROM documents WHERE category = ?", (category,)).fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM documents WHERE category = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (category, page_size, (page - 1) * page_size),
        ).fetchall()
    else:
        total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (page_size, (page - 1) * page_size),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows], total


def get_all_documents() -> list[dict]:
    """获取所有文档（用于 ChromaDB 同步）"""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM documents ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categories() -> list[str]:
    """获取所有不重复的文档分类"""
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT category FROM documents ORDER BY category").fetchall()
    conn.close()
    return [r["category"] for r in rows]


# ==================== 会话管理（新增）====================

def create_session(user_id: int, title: str = "新对话") -> int:
    """创建会话，返回会话 ID"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO chat_sessions (user_id, session_title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (user_id, title, now, now),
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_user_sessions(user_id: int) -> list[dict]:
    """获取用户的所有会话，按更新时间倒序"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, (SELECT COUNT(*) FROM chat_messages WHERE session_id = s.id) AS message_count
           FROM chat_sessions s WHERE s.user_id = ? ORDER BY s.updated_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_by_id(session_id: int) -> dict | None:
    """根据 ID 查询会话"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_session_messages(session_id: int, user_id: int) -> list[dict]:
    """获取会话的所有消息，按时间正序"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? AND user_id = ? ORDER BY created_at ASC",
        (session_id, user_id),
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        # 反序列化 citations JSON
        if d.get("citations"):
            import json
            try:
                d["citations"] = json.loads(d["citations"])
            except (json.JSONDecodeError, TypeError):
                d["citations"] = None
        results.append(d)
    return results


def save_message(session_id: int, user_id: int, role: str, content: str, citations: str | None = None) -> int:
    """保存消息，返回消息 ID"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO chat_messages (session_id, user_id, role, content, citations, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, user_id, role, content, citations, now),
    )
    msg_id = cur.lastrowid
    # 更新会话时间
    conn.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (now, session_id))
    # 自动更新会话标题（首次用户消息的前 30 字符）
    if role == "user":
        session = conn.execute("SELECT session_title FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
        if session and session["session_title"] == "新对话":
            title = content[:30] + ("..." if len(content) > 30 else "")
            conn.execute("UPDATE chat_sessions SET session_title = ? WHERE id = ?", (title, session_id))
    conn.commit()
    conn.close()
    return msg_id
