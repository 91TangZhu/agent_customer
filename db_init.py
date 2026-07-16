"""
SQLite 数据库初始化脚本
运行方式：
    conda activate agent_customer
    python db_init.py
执行后会在 data/ 目录下生成 customer.db 文件，包含服装电商测试数据和知识库结构。
"""
import sqlite3
import os
from datetime import datetime, timedelta


DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "customer.db")


def init_db():
    """创建所有表结构 + 插入服装电商测试数据"""
    os.makedirs(DB_DIR, exist_ok=True)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"[CLEAN] 已删除旧数据库: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ==================== 统一用户表（合并原 users + auth_users）====================
    cur.execute("""
        CREATE TABLE users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            phone         TEXT    UNIQUE,
            is_admin      INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT    NOT NULL
        )
    """)

    # ==================== 订单表 ====================
    cur.execute("""
        CREATE TABLE orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            order_no     TEXT    NOT NULL UNIQUE,
            product_name TEXT    NOT NULL,
            amount       REAL    NOT NULL,
            status       TEXT    NOT NULL DEFAULT '待付款',
            created_at   TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ==================== 物流表 ====================
    cur.execute("""
        CREATE TABLE logistics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL UNIQUE,
            tracking_no TEXT    NOT NULL,
            carrier     TEXT    NOT NULL,
            status      TEXT    NOT NULL,
            updates     TEXT,
            created_at  TEXT    NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    # ==================== 知识库文档表 ====================
    cur.execute("""
        CREATE TABLE documents (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            category   TEXT    NOT NULL DEFAULT '通用',
            gender     TEXT    NOT NULL DEFAULT '通用',
            created_at TEXT    NOT NULL,
            updated_at TEXT    NOT NULL
        )
    """)

    # ==================== 会话表 ====================
    cur.execute("""
        CREATE TABLE chat_sessions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            session_title TEXT    NOT NULL DEFAULT '新对话',
            created_at    TEXT    NOT NULL,
            updated_at    TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ==================== 聊天消息表 ====================
    cur.execute("""
        CREATE TABLE chat_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            role       TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
            content    TEXT    NOT NULL,
            citations  TEXT,
            created_at TEXT    NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    print("[OK] 6 张表创建完成: users, orders, logistics, documents, chat_sessions, chat_messages")

    # ==================== 密码哈希 ====================
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    pw_hash = pwd_ctx.hash("123456")

    # ==================== 插入用户数据（6人，密码均为 123456）====================
    now = datetime.now()
    users = [
        ("admin",    pw_hash, "13800000001", 1, now - timedelta(days=90)),
        ("testuser", pw_hash, "13800000002", 0, now - timedelta(days=60)),
        ("lihua",    pw_hash, "13800138001", 0, now - timedelta(days=45)),
        ("wangfang", pw_hash, "13800138002", 0, now - timedelta(days=30)),
        ("zhangwei", pw_hash, "13800138003", 0, now - timedelta(days=15)),
        ("chenjing", pw_hash, "13800138004", 0, now - timedelta(days=3)),
    ]
    cur.executemany(
        "INSERT INTO users (username, password_hash, phone, is_admin, created_at) VALUES (?, ?, ?, ?, ?)",
        [(u[0], u[1], u[2], u[3], u[4].strftime("%Y-%m-%d %H:%M:%S")) for u in users],
    )
    print(f"[OK] 插入 {len(users)} 条用户数据 (admin / testuser / lihua / wangfang / zhangwei / chenjing)")

    # ==================== 插入订单数据（8条服装商品）====================
    orders = [
        (1, "ORD20260701001", "高端羊毛混纺大衣 驼色 M",        1599.00, "已完成", now - timedelta(days=13)),
        (1, "ORD20260701002", "夏季纯棉圆领T恤 白色 L",          129.00, "已发货", now - timedelta(days=5)),
        (2, "ORD20260702001", "真丝连衣裙 碎花 S",              899.00, "已完成", now - timedelta(days=20)),
        (2, "ORD20260702002", "莫代尔打底衫 黑色 L",             99.00, "待付款", now - timedelta(days=1)),
        (3, "ORD20260703001", "商务休闲修身西裤 黑色 32码",       399.00, "已发货", now - timedelta(days=3)),
        (3, "ORD20260703002", "弹力牛仔小脚裤 深蓝 29码",         259.00, "已完成", now - timedelta(days=25)),
        (4, "ORD20260704001", "冰丝防晒外套 UPF50+ 浅灰 均码",    299.00, "已退款", now - timedelta(days=7)),
        (5, "ORD20260705001", "天丝亚麻阔腿裤 米白 M",           329.00, "待付款", now - timedelta(hours=2)),
    ]
    cur.executemany(
        "INSERT INTO orders (user_id, order_no, product_name, amount, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(o[0], o[1], o[2], o[3], o[4], o[5].strftime("%Y-%m-%d %H:%M:%S")) for o in orders],
    )
    print(f"[OK] 插入 {len(orders)} 条订单数据（全部服装商品）")

    # ==================== 插入物流数据（5条）====================
    logistics = [
        (1, "SF1234567890", "顺丰速运", "已签收", "2026-07-12 14:30 已签收，签收人：本人"),
        (2, "SF1234567891", "顺丰速运", "运输中", "2026-07-13 08:00 快件到达【北京分拣中心】"),
        (3, "JD9876543210", "京东物流", "已签收", "2026-07-05 10:15 已签收"),
        (5, "YT5678901234", "圆通速递", "运输中", "2026-07-12 20:00 快件离开【上海转运中心】"),
        (6, "SF1234567892", "顺丰速运", "已签收", "2026-07-02 09:45 已签收"),
    ]
    cur.executemany(
        "INSERT INTO logistics (order_id, tracking_no, carrier, status, updates, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(l[0], l[1], l[2], l[3], l[4], now.strftime("%Y-%m-%d %H:%M:%S")) for l in logistics],
    )
    print(f"[OK] 插入 {len(logistics)} 条物流数据")

    # ==================== 提交 ====================
    conn.commit()
    conn.close()

    # 输出统计
    size_kb = os.path.getsize(DB_PATH) / 1024
    print(f"\n===== 数据库初始化完成! =====")
    print(f"   文件位置: {DB_PATH}")
    print(f"   文件大小: {size_kb:.1f} KB")
    print(f"   表数量:   6 (users, orders, logistics, documents, chat_sessions, chat_messages)")
    print(f"   数据:     {len(users)} 用户 + {len(orders)} 订单 + {len(logistics)} 物流")
    print(f"   登录账号: admin/123456 (管理员), testuser/123456 (普通用户)")
    print(f"   其他用户: lihua, wangfang, zhangwei, chenjing (密码均为 123456)")


def init_kb():
    """初始化知识库种子数据（向量库）—— 在服务启动后通过 API 调用"""
    print("[SKIP] 知识库种子数据需在服务启动后通过 POST /admin/kb/init 初始化（依赖嵌入模型加载）")
    print("       启动服务后使用管理员账号（admin / 123456）登录，点击「初始化默认知识库」按钮即可")


if __name__ == "__main__":
    init_db()
    print()
    init_kb()
