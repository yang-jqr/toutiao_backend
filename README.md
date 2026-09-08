# AI 掘金头条后端（模块化整合版）

把 day01~day06 一步步累加的代码，整合成一个**按模块划分文件**的完整项目（`toutiao_backend/`）。
启动即用：自动建库建表 + 填充种子数据，无需手动执行 SQL。

## 目录结构

```
toutiao_backend/
├── main.py                  # 入口：创建应用 + 全局异常 + CORS + 挂载路由 + 启动建库
├── init_db.py               # 首次运行：自动建库 → 建表 → 填充种子数据
├── test_main.http           # 接口测试用例（VS Code REST Client）
├── config/
│   ├── db_conf.py           # MySQL 异步引擎 + get_db 依赖
│   └── cache_conf.py        # Redis 连接 + 缓存读写封装
├── models/                  # SQLAlchemy ORM（统一 Base）
│   ├── base.py  users.py  news.py  favorite.py  history.py
├── schemas/                 # Pydantic 请求/响应校验
│   ├── base.py  users.py  news.py  favorite.py  history.py
├── crud/                    # 业务层：封装数据库操作
│   ├── users.py  news.py  news_cache.py  favorite.py  history.py
├── cache/
│   └── news_cache.py        # 新闻缓存 key 规则（Redis 缓存旁路）
├── utils/
│   ├── auth.py              # get_current_user 依赖（Token 校验）
│   ├── security.py          # bcrypt 密码加密/验证
│   ├── response.py          # 统一响应 {code, message, data}
│   ├── exception.py         # 各异常处理器实现
│   └── exception_handlers.py# 全局异常注册
└── routers/                 # 路由层（接口）
    ├── news.py  users.py  favorite.py  history.py
```

## 运行

前置：本机已启动 **MySQL(3306)** 与 **Redis(6379)**。

```bash
# 进入项目目录
cd toutiao_backend

# 1) 配置环境变量（复制示例并填入你的 MySQL 密码）
cp .env.example .env     # Windows: copy .env.example .env
#    然后编辑 .env，把 DB_PASSWORD 改成你的 MySQL 密码

# 2) 安装依赖（任选）
pip install "fastapi==0.125.0" "uvicorn==0.38.0" "sqlalchemy==2.0.45" \
  "pydantic==2.12.5" "passlib==1.7.4" "bcrypt==3.2.2" "redis==7.1.0" \
  "aiomysql==0.3.2" "python-dotenv==1.2.1"

# 3) 启动
uvicorn main:app --reload --port 8000
```

首次启动会自动创建 `news_app` 库、建好 6 张表、填充 8 个分类与若干新闻。
接口文档：http://127.0.0.1:8000/docs

> `.env` 已在 `.gitignore` 中忽略，不会上传 GitHub；仓库只提交无密码的 `.env.example`。

## 配置项（环境变量 / .env 文件）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DB_USER` / `DB_PASSWORD` | `root` / 空 | MySQL 账号密码（密码必须填） |
| `DB_HOST` / `DB_PORT` | `localhost` / `3306` | MySQL 地址 |
| `DB_NAME` | `news_app` | 数据库名 |
| `DB_ECHO` | `0` | `1` 时打印 SQL 日志 |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | `localhost` / `6379` / `0` | Redis |

## 接口清单（22 条）

| 模块 | 接口 |
|---|---|
| 新闻 | `GET /api/news/categories` · `GET /api/news/list` · `GET /api/news/detail?id=` |
| 用户 | `POST /api/user/register` · `POST /api/user/login` · `GET /api/user/info` · `PUT /api/user/update` · `PUT /api/user/password` |
| 收藏 | `GET /api/favorite/check` · `POST /api/favorite/add` · `DELETE /api/favorite/remove` · `GET /api/favorite/list` · `DELETE /api/favorite/clear` |
| 历史 | `POST /api/history/add` · `GET /api/history/list` · `DELETE /api/history/delete/{id}` · `DELETE /api/history/clear` |

收藏/历史需登录，请求头带 `Authorization: Bearer <token>`。

## 与课程 day01~day06 的对应

| 天数 | 内容 | 本项目中位置 |
|---|---|---|
| day01–02 | FastAPI 基础 / ORM | models、schemas、routers |
| day03 | 新闻模块 | routers/news.py · crud/news.py · models/news.py |
| day04 | 用户模块 + 安全 | routers/users.py · crud/users.py · utils/* |
| day05 | 收藏与历史 | routers/favorite|history.py · crud/favorite|history.py |
| day06 | Redis 缓存 + 模型序列化 | cache/* · crud/news_cache.py |

> 注：项目根目录还有一份单文件版 `app.py`（功能相同、写法不同），两者可任选；不需要可删除。