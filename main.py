# ============================================================
# 项目入口：main.py —— FastAPI 应用的主文件
# 职责：创建应用 → 注册全局异常处理 → 配置跨域 → 挂载各模块路由
# ============================================================

# 1. 导入核心类
from fastapi import FastAPI                       # FastAPI：应用主类，用于创建应用实例
from routers import news, users, favorite, history  # 导入四个模块的路由对象（新闻/用户/收藏/历史）
from fastapi.middleware.cors import CORSMiddleware  # CORSMiddleware：跨域中间件（解决前后端不同端口访问问题）

from utils.exception_handlers import register_exception_handlers  # 导入异常处理器注册函数

from init_db import init_db  # 首次运行自动建库建表 + 种子数据


# 2. 创建 FastAPI 应用实例（所有接口的容器）
app = FastAPI()

# 2.5 启动时初始化数据库（库 → 表 → 种子数据）
# init_db() 内部三步：① 用不带库名的 SERVER_DATABASE_URL 建库（CREATE DATABASE IF NOT EXISTS）
#   ② 用 Base.metadata.create_all 建出所有表 ③ 表为空时才写入种子数据，重复启动不会重复插入
# 用 try...except 包住：初始化失败（比如 MySQL 没启动）只打印日志，不抛异常阻断应用启动
@app.on_event("startup")  # 注册启动事件：应用启动完成后自动执行 on_startup()
async def on_startup():
    try:
        await init_db()  # 建库 → 建表 → 空库则填种子数据
        print("[init] 数据库就绪：建表完成，种子数据已填充。")
    except Exception as e:
        print(f"[init] 初始化数据库失败（请确认 MySQL 已启动且账号密码正确）：{e}")

# 3. 注册异常处理器（把项目内各种异常统一转成 code/message/data 格式返回）
register_exception_handlers(app)


# 4. 添加跨域中间件（前后端分离必配）
# 作用：允许浏览器跨域名/跨端口请求本后端，否则前端 fetch/axios 会被浏览器拦截
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 允许的源（协议+域名+端口），* 表示允许所有源，开发阶段使用，生产环境需指定具体源
    allow_credentials=True,  # 允许跨域请求携带 Cookie 凭证
    allow_methods=["*"],     # 允许所有 HTTP 方法（GET/POST/PUT/DELETE 等）
    allow_headers=["*"],     # 允许所有请求头
)


# 5. 根路径接口（测试服务是否启动）
@app.get("/")  # 装饰器：把 root 函数注册为 GET / 的处理函数
async def root():  # 定义异步处理函数（async 提升并发性能）
    return {"message": "Hello World"}  # 返回字典，FastAPI 会自动把它序列化为 JSON 响应

# 6. 挂载路由/注册路由
# 把各个模块的路由对象挂载到 app 上，这样 /api/news、/api/user 等接口才生效
app.include_router(news.router)      # 新闻模块路由（/api/news）
app.include_router(users.router)     # 用户模块路由（/api/user）
app.include_router(favorite.router)  # 收藏模块路由（/api/favorite）
app.include_router(history.router)   # 历史记录模块路由（/api/history）
