# ============================================================
# 数据库配置：config/db_conf.py
# 职责：创建异步引擎 + 会话工厂 + 提供 get_db 依赖项（每请求一个会话）
# ============================================================

# 导入 SQLAlchemy 异步组件：创建引擎 / 创建会话工厂 / 会话类型
import os

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

# 1. 数据库连接 URL
# 格式：mysql+aiomysql://用户名:密码@主机:端口/库名?charset=编码
# 配置从 .env 读取（见项目根目录 .env.example），代码内不含任何明文密码
load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # 必须通过 .env 或环境变量提供
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "news_app")

# 不带库名（用于建库）
SERVER_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
# 带库名（应用使用）
ASYNC_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 2. 创建异步引擎（管理数据库连接池）
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("DB_ECHO", "0") == "1",  # 需要 SQL 日志时设 DB_ECHO=1
    pool_size=10,  # 设置连接池中保持的持久连接数
    max_overflow=20  # 设置连接池允许创建的额外连接数
)

# 3. 创建异步会话工厂（会话 = 操作数据库的"手"，事务 + 增删改查都靠它）
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,       # 绑定引擎
    class_=AsyncSession,     # 指定会话类型为异步会话
    expire_on_commit=False   # 提交后对象不过期，避免再次查库
)


# 4. 依赖项 get_db：供路由通过 Depends(get_db) 注入数据库会话
# 使用生成器 + async with：请求进来开一个会话 → 用完自动关闭
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session          # 把会话交给路由使用
            await session.commit()  # 路由逻辑执行完，自动提交事务
        except Exception:
            await session.rollback()  # 出错则回滚，保证数据一致性
            raise
        finally:
            await session.close()     # 最后关闭会话，归还连接
