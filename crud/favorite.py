# ============================================================
# crud 层：favorite.py —— 收藏模块的数据库操作
# 职责：封装所有对收藏表的增删改查，供路由层调用
# ============================================================

# 导入查询构建工具：select 查询 / delete 删除 / func SQL函数
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession  # 异步会话类型（类型标注用）

from models.favorite import Favorite  # 收藏表模型
from models.news import News          # 新闻表模型（联表查询用）


# 检查收藏状态：当前用户 是否 收藏了这一条新闻
async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    # 按 用户id + 新闻id 精确查询收藏记录
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    # 是否有收藏记录：查到了返回 True，没查到返回 False
    return result.scalar_one_or_none() is not None


# 添加收藏：往收藏表插入一条记录
async def add_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    favorite = Favorite(user_id=user_id, news_id=news_id)  # 创建收藏对象（内存中）
    db.add(favorite)      # 登记到会话（不碰数据库）
    await db.commit()     # 提交事务（真正写入）
    await db.refresh(favorite)  # 从数据库读回最新数据（拿到自增id等）
    return favorite       # 返回收藏对象


# 取消收藏：删除该用户对某条新闻的收藏记录
async def remove_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    # 按 用户id + 新闻id 删除
    stmt = delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0  # 受影响行数 > 0 → 删除成功


# 获取收藏列表：获取的是某个用户的收藏列表 + 分页功能
async def get_favorite_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):
    # 第1步：查总量（该用户收藏了多少条，用于分页）
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 第2步：获取收藏列表 - 联表查询 join() + 收藏时间排序 + 分页
    # 语法：select(查询主体模型类, 字段别名).join(联合查询的模型类, 联合查询的条件).where().order_by().offset().limit()
    # 别名：Favorite.created_at.label("favorite_time") 给字段起别名
    offset = (page - 1) * page_size  # 计算跳过条数
    # 查询结果每行结构：
    # [
    #   (新闻对象, 收藏时间, 收藏id)
    # ]
    query = (select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id"))  # 查新闻 + 收藏时间 + 收藏id
             .join(Favorite, Favorite.news_id == News.id)   # 联表：收藏表.news_id = 新闻表.id
             .where(Favorite.user_id == user_id)            # 条件：该用户的收藏
             .order_by(Favorite.created_at.desc())          # 排序：按收藏时间倒序（最新在前）
             .offset(offset).limit(page_size)               # 分页：跳过 offset 条，取 page_size 条
             )
    result = await db.execute(query)
    rows = result.all()  # 取出所有行（元组列表）
    return rows, total   # 返回列表 + 总数


# 清空收藏列表：当前用户的收藏列表
async def remove_all_favorites(
        db: AsyncSession,
        user_id: int
):
    # 按用户id删除所有收藏记录
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()

    # 返回一个删除的数量（rowcount 可能为 0，用 or 0 兜底）
    return result.rowcount or 0
