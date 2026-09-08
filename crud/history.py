# ============================================================
# crud 层：history.py —— 浏览历史模块的数据库操作
# 职责：封装所有对历史表的增删改查，供路由层调用
# ============================================================

from datetime import datetime  # 时间模块（用于刷新浏览时间）

# 导入查询构建工具：select 查询 / func SQL函数 / delete 删除
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession  # 异步会话类型（类型标注用）

from models.history import History  # 历史表模型
from models.news import News        # 新闻表模型（联表查询用）


# 添加历史记录：已看过 → 刷新浏览时间；没看过 → 新增一条
async def add_history(db: AsyncSession, user_id: int, news_id: int):
    """
    添加历史记录
    """
    # 第1步：查该用户是否已经看过这条新闻
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    existing_history = result.scalar_one_or_none()
    if existing_history:  # 已存在 → 只更新浏览时间（去重，避免重复记录）
        existing_history.view_time = datetime.now()  # 刷新浏览时间
        await db.commit()          # 提交更新
        await db.refresh(existing_history)  # 读回最新数据
        return existing_history
    else:  # 不存在 → 新增一条历史记录
        history = History(user_id=user_id, news_id=news_id)
        db.add(history)      # 登记到会话
        await db.commit()    # 写入数据库
        await db.refresh(history)  # 读回最新数据
        return history


# 获取历史记录列表：联表查询（历史 + 新闻）+ 分页
async def get_history_list(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size  # 计算跳过条数
    # 第1步：查总量
    count_query = select(func.count(History.id)).where(History.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 第2步：联表查询（新闻 + 浏览时间 + 历史id），按浏览时间倒序 + 分页
    query = (select(News, History.view_time.label("view_time"), History.id.label("history_id"))  # 查新闻 + 浏览时间 + 历史id
             .join(History, History.news_id == News.id)   # 联表：历史表.news_id = 新闻表.id
             .where(History.user_id == user_id)           # 条件：该用户的记录
             .order_by(History.view_time.desc())          # 排序：浏览时间倒序（最新在前）
             .offset(offset).limit(page_size))            # 分页

    result = await db.execute(query)
    rows = result.all()  # 每行：(新闻对象, 浏览时间, 历史id)
    return rows, total   # 返回列表 + 总数


# 删除历史记录
async def delete_history(db: AsyncSession, user_id: int, news_id: int):
    """
    删除历史记录
    """
    # 按 用户id + 新闻id 删除
    query = delete(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    await db.commit()

    return result.rowcount > 0  # 受影响行数 > 0 → 删除成功


# 清空历史记录
async def clear_history(db: AsyncSession, user_id: int):
    """
    清空历史记录
    """
    # 按用户id删除所有历史记录
    query = delete(History).where(History.user_id == user_id)
    result = await db.execute(query)
    await db.commit()

    return result.rowcount or 0  # 返回删除条数（0 兜底）