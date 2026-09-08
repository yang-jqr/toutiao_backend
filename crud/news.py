# ============================================================
# crud 层：news.py —— 新闻模块的数据库操作
# 职责：封装所有对新闻表/分类表的查询与更新，供路由层调用
# ============================================================

# 导入查询构建工具：select 查询 / func SQL函数 / update 更新
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession  # 异步会话类型（类型标注用）
from models.news import Category, News           # 导入模型类：分类、新闻


# 查询所有新闻分类（支持分页）
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(Category).offset(skip).limit(limit)  # 跳过 skip 条，最多取 limit 条
    result = await db.execute(stmt)
    return result.scalars().all()  # 取出所有 Category 对象


# 查询指定分类下的新闻列表（分页）
async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    # 查询的是指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)  # WHERE 分类=指定值 + 分页
    result = await db.execute(stmt)
    return result.scalars().all()


# 查询指定分类下的新闻数量（用于分页计算总量）
async def get_news_count(db: AsyncSession, category_id: int):
    # 查询的是指定分类下的新闻数量
    stmt = select(func.count(News.id)).where(News.category_id == category_id)  # COUNT(id) + 限定分类
    result = await db.execute(stmt)
    return result.scalar_one()  # 只能有一个结果，否则报错


# 查询单条新闻详情
async def get_news_detail(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)  # 按 id 精确查询
    result = await db.execute(stmt)
    return result.scalar_one_or_none()  # 最多一条；查不到返回 None（供路由判断"新闻是否存在"）


# 浏览量 +1，返回是否更新成功
async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)  # UPDATE：views = views + 1（SQL 原子操作）
    result = await db.execute(stmt)
    await db.commit()

    # 更新 → 检查数据库是否真的命中了数据 → 命中了返回True
    return result.rowcount > 0  # rowcount 为受影响行数；>0 说明 id 存在


# 查询相关新闻（同分类、排除自己、按热度+时间排序）
async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    # order_by 排序 → 浏览量和发布时间
    stmt = select(News).where(
        News.category_id == category_id,  # 条件1：同一分类
        News.id != news_id                # 条件2：不是当前新闻本身
    ).order_by(
        News.views.desc(),  # 默认是升序，desc 表示降序（最热在前）
        News.publish_time.desc()  # 浏览量相同再按时间倒序（最新在前）
    ).limit(limit)  # 最多返回 limit 条
    result = await db.execute(stmt)
    # return result.scalars().all()
    related_news = result.scalars().all()
    # 列表推导式 推导出新闻的核心数据，然后再 return（转成前端友好的驼峰字典）
    return [{
        "id": news_detail.id,
        "title": news_detail.title,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": news_detail.views
    } for news_detail in related_news]
