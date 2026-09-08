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
@app.on_event("startup")
async def on_startup():
    try:
        await init_db()
        print("[init] 数据库就绪：建表完成，种子数据已填充。")
    except Exception as e:
        print(f"[init] 初始化数据库失败（请确认 MySQL 已启动且账号密码正确）：{e}")

# 3. 注册异常处理器（把项目内各种异常统一转成 code/message/data 格式返回）
register_exception_handlers(app)


# 4. 添加跨域中间件（前后端分离必配）
# 作用：允许浏览器跨域名/跨端口请求本后端，否则前端 fetch/axios 会被浏览器拦截
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 允许的源，开发阶段允许所有源，生产环境需要指定源
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],     # 允许的请求方法
    allow_headers=["*"],     # 允许的请求头
)


# 5. 根路径接口（测试服务是否启动）
@app.get("/")
async def root():
    return {"message": "Hello World"}

# 6. 挂载路由/注册路由
# 把各个模块的路由对象挂载到 app 上，这样 /api/news、/api/user 等接口才生效
app.include_router(news.router)      # 新闻模块路由（/api/news）
app.include_router(users.router)     # 用户模块路由（/api/user）
app.include_router(favorite.router)  # 收藏模块路由（/api/favorite）
app.include_router(history.router)   # 历史记录模块路由（/api/history）
