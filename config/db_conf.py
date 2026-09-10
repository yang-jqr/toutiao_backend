# ============================================================
# 数据库配置：config/db_conf.py
# 职责：创建异步引擎 + 会话工厂 + 提供 get_db 依赖项（每请求一个会话）
# ============================================================

# 导入 SQLAlchemy 异步组件：创建引擎 / 创建会话工厂 / 会话类型
import os  # os：读取环境变量（数据库账号密码来自 .env）

from dotenv import load_dotenv  # load_dotenv：把 .env 文件里的配置加载成环境变量

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
# async_sessionmaker : 异步会话工厂，用于创建数据库会话
# AsyncSession       : 异步会话类型（用于类型标注）
# create_async_engine: 创建异步数据库引擎（连接的核心对象）

# 1. 数据库连接 URL
# 格式：mysql+aiomysql://用户名:密码@主机:端口/库名?charset=编码
# mysql+aiomysql   : 使用 aiomysql 驱动连接 MySQL（支持异步）
# 用户名:密码       : 由 DB_USER / DB_PASSWORD 从 .env 注入（课件里写死的明文密码已改为环境变量）
# 主机:端口         : 由 DB_HOST / DB_PORT 从 .env 注入，默认 localhost:3306
# 库名              : 由 DB_NAME 从 .env 注入，默认 news_app
# charset=utf8mb4   : 使用 utf8mb4 字符集，支持 emoji 等四字节字符
# 配置从 .env 读取（见项目根目录 .env.example），代码内不含任何明文密码
load_dotenv()  # 读取 .env，把配置注入 os.environ

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # 必须通过 .env 或环境变量提供
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "news_app")

# 不带库名（用于建库）：init_db 先用它连 MySQL 执行 CREATE DATABASE IF NOT EXISTS，
#   此时库还不存在，所以连接串里不能带库名
SERVER_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
# 带库名（应用使用）：运行时所有增删改查都走这条，交给下面的引擎 / 会话工厂
ASYNC_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 2. 创建异步引擎（管理数据库连接池）
async_engine = create_async_engine(  # 调用函数创建异步引擎（数据库连接的核心对象）
    ASYNC_DATABASE_URL,  # 传入数据库连接串
    echo=os.getenv("DB_ECHO", "0") == "1",  # echo：在控制台输出实际执行的 SQL 日志，方便调试；由 .env 的 DB_ECHO=1 打开
    pool_size=10,  # 连接池中保持的持久连接数（常驻 10 个）
    max_overflow=20  # 连接池允许额外创建的最大连接数（峰值最多 10+20=30 个）
)

# 3. 创建异步会话工厂（会话 = 操作数据库的"手"，事务 + 增删改查都靠它）
AsyncSessionLocal = async_sessionmaker(  # 调用函数创建会话工厂
    bind=async_engine,       # 绑定引擎
    class_=AsyncSession,     # 指定会话类型为异步会话
    expire_on_commit=False   # 提交后对象不过期，避免再次查库
)


# 4. 依赖项 get_db：供路由通过 Depends(get_db) 注入数据库会话
# 使用生成器 + async with：请求进来开一个会话 → 用完自动关闭
async def get_db():  # 定义异步生成器函数：给路由"借"一个会话，并负责善后（提交/回滚/关闭）
    async with AsyncSessionLocal() as session:  # 创建会话并进入上下文管理器（退出时自动关闭）
        try:
            yield session          # 把会话"产出"给调用方（路由函数），函数在此暂停
            await session.commit()  # 路由逻辑执行完，自动提交事务（写入数据库）
        except Exception:  # 若执行过程中出现任何异常
            await session.rollback()  # 出错则回滚，保证数据一致性
            raise  # 继续向上抛出异常（交给 FastAPI 返回 500，不让错误被吞掉）
        finally:
            await session.close()     # 最后关闭会话，归还连接
