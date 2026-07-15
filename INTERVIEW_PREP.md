# 面试准备 — 阶段性总结

> 每次完成阶段性功能后更新本文档，方便面试前快速回顾。
> 最后更新: 2026-07-15 | 当前版本: v0.2.0

---

## 一、一句话概括项目

从零搭建了一个**基于大语言模型的服装电商智能客服系统**，用户用自然语言提问（比如"帮我查手机号13800138001的订单"），AI 自动理解意图、调用工具查数据库、返回格式化结果。v0.2.0 升级为 RAG 知识库问答系统，支持 JWT 用户认证、多轮对话、知识库管理。

---

## 二、技术栈（面试官必问）

| 层级 | v0.1.0 | v0.2.0 升级 |
|------|--------|-------------|
| **Web 框架** | FastAPI + Uvicorn | 同左 |
| **AI 编排** | LangChain + LangGraph (ReAct) | 同左 |
| **大模型** | DeepSeek v4 Flash/Pro | 同左 |
| **数据库** | SQLite (3张表) | SQLite (7张表) + ChromaDB 向量库 |
| **向量模型** | — | text2vec-base-chinese |
| **认证** | — | JWT + bcrypt |
| **前端** | 单页聊天 | 多页面: 登录/注册 → 聊天+侧栏+引用 → 知识库管理后台 |

---

## 三、项目架构演进

### v0.1.0: ReAct Agent 工具调用

```
用户浏览器(中文聊天页)
    ↓ HTTP POST /chat
FastAPI 入口(main.py)
    ↓ 转发消息
LangChain ReAct Agent(agent.py)
    ↓ 选择工具
┌───────────────┼───────────────┐
查用户(按手机)  查订单(按用户/订单号)  查物流
    ↓               ↓               ↓
           SQLite 数据库
```

### v0.2.0: RAG 知识库 + 认证 + 多轮对话

```
用户浏览器(多页面: 登录/注册 → 聊天 → 知识库管理)
    ↓ JWT Token
FastAPI(中间件: 鉴权 + 日志)
    ↓
LangChain ReAct Agent
    ├── 工具调用: 查用户/查订单/查物流
    ├── RAG 检索: 向量搜索知识库(19条服装知识)
    └── 上下文: 多轮对话历史
         ↓
SQLite(业务数据) + ChromaDB(向量库)
```

---

## 四、核心模块一览

```
app/
├── main.py          # FastAPI 入口 + 多页面路由
├── agent.py         # LangChain ReAct Agent
├── tools.py         # Agent 工具函数
├── models.py        # Pydantic 数据模型
├── database.py      # SQLite 查询封装
├── auth.py          # JWT 认证 + bcrypt 密码哈希
├── rag.py           # RAG 检索引擎 (ChromaDB)
├── logger.py        # 请求日志中间件
├── middleware.py    # 鉴权中间件
└── kb_seed_data.py  # 知识库初始化 (19条服装知识)
```

---

## 五、数据库设计 (v0.2.0)

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `users` | 用户信息 | phone, email |
| `orders` | 订单数据 | order_no, product_name, amount, status |
| `logistics` | 物流追踪 | tracking_no, carrier, status |
| `auth_users` | 认证用户 | username, hashed_password, role |
| `documents` | 知识库文档 | title, content, category |
| `chat_sessions` | 对话会话 | user_id, title |
| `chat_messages` | 聊天记录 | session_id, role, content |

---

## 六、踩过的坑 & 解决方案（面试加分项）

| 坑 | 解决方案 | 涉及知识点 |
|----|----------|-----------|
| DeepSeek 老模型下线 | 改用 `deepseek-v4-flash`，API 参数从 `model=` → `model_name=` | API 版本兼容 |
| Windows GBK 编码错误 | emoji → ASCII 标记 `[OK]` `[CLEAN]` | 字符编码、跨平台 |
| GitHub 22 端口被墙 | SSH 配置走 `ssh.github.com:443` | 网络、SSH |
| Swagger 英文太多 | 内嵌中文聊天 HTML 页面 | 用户体验 |
| Claude Code 技能格式 | 3种格式踩坑，最终 `skills/<名>/SKILL.md` | 工具链 |
| 向量检索结果不精准 | 调优 chunk size + 中文向量模型选择 | RAG 优化 |

---

## 七、工程化实践

1. **环境隔离** — Conda 虚拟环境，不污染系统 Python
2. **密钥安全** — `.env` 存密钥，`.gitignore` 防止泄露，`.env.example` 供团队参考
3. **项目记忆系统** — `PROJECT_SUMMARY.md`(静态档案) + `CLAUDE_PROGRESS.md`(开发时间线)，新会话通过 `/project-init` 秒恢复上下文
4. **AI 辅助开发** — Claude Code 自定义 Skills (`/project-init` `/project-update` `/git-push`) + `record-keeper` Agent 自动归档
5. **Git 规范** — 每次提交有明确 message，禁止 force push
6. **日志系统** — 请求日志中间件，全链路可追踪

---

## 八、后续方向

| 优先级 | 功能 | 涉及技术 |
|--------|------|----------|
| P2 | 退换货工具 | Agent 工具扩展 |
| P2 | 知识库文档 CRUD | 管理后台完善 |
| P3 | Docker 容器化部署 | Docker + Nginx |
| P3 | 对接企业 IM | 飞书/企微 Bot API |

---

## 九、面试话术

### 30秒版本
> "我从零搭建了一个服装电商智能客服系统，用 FastAPI + LangChain + DeepSeek，实现了 ReAct Agent 自动调用工具查询订单物流，v0.2.0 升级为 RAG 知识问答系统，接入了 ChromaDB 向量检索和 JWT 认证，支持多轮对话。全程独立完成架构设计、数据库建模、前后端开发和工程化配置。"

### 关键词自查
- [ ] 能解释 ReAct Agent 的 Think → Act → Observe 循环
- [ ] 能解释 RAG 的原理：Embedding → 向量检索 → 上下文增强
- [ ] 能对比 FastAPI vs Flask 的优劣势
- [ ] 能讲清楚 JWT 认证流程
- [ ] 能解释为什么用 SQLite + ChromaDB 双存储
- [ ] 能说清楚 ChromaDB 和传统数据库的区别

---

## 十、版本记录

| 日期 | 版本 | 主要变化 |
|------|------|----------|
| 2026-07-15 | v0.2.0 | RAG 知识库 + JWT 认证 + 多轮对话 + 知识库管理后台 |
| 2026-07-14 | v0.1.0 | 项目初始化，ReAct Agent + 4工具 + 中文聊天页 |

---

> 面试前翻一遍，重点看「架构演进」「踩坑」「面试话术」三个章节。
