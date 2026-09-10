# ============================================================
# crud 层：favorite.py —— 收藏模块的数据库操作
# 职责：封装所有对收藏表(favorite)的增删改查，供路由层调用
# ============================================================

# 导入查询构建工具：select 查询 / delete 删除 / func SQL函数(count/求和等)
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession  # 异步会话类型（用于参数类型标注，仅提示作用）

from models.favorite import Favorite  # 收藏表模型（对应 favorite 表）
from models.news import News          # 新闻表模型（联表查询时要用到）


# 检查收藏状态：当前用户 是否 收藏了这一条新闻
# 用途：前端展示"收藏/未收藏"按钮状态时调用
async def is_news_favorite(
        db: AsyncSession,     # 数据库会话（依赖注入传入）
        user_id: int,         # 当前用户id
        news_id: int          # 要检查的新闻id
):
    # 按 用户id + 新闻id 两个条件 精确查询收藏记录（两个条件用逗号连接 = AND）
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)  # 执行查询，返回结果集
    # scalar_one_or_none()：取唯一一行；没有则返回 None
    # 是否有收藏记录：查到记录(不是None) → True(已收藏)；没查到(None) → False(未收藏)
    return result.scalar_one_or_none() is not None


# 添加收藏：往收藏表插入一条记录
async def add_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    favorite = Favorite(user_id=user_id, news_id=news_id)  # 创建一个 Favorite 对象（此时只存在于内存中，还没碰数据库）
    # 为什么是 add 不是 update？
    # - 这里 favorite 是【新建】的对象：数据库里还没有这条收藏记录，属于"新增"操作
    # - add 对"新对象" → commit 时生成的是 INSERT 语句（插入新行）
    # - update 是用来改"已存在记录"的（如改密码/改用户信息），此处场景不符
    # 结论：新增用 add，更新用 update，二者对应 SQL 的 INSERT / UPDATE
    db.add(favorite)      # 登记到会话（把对象加入待处理列表，此时仍未写库）
    await db.commit()     # 提交事务 → 真正 INSERT 写入数据库（到这里才生效）
    await db.refresh(favorite)  # 从数据库读回最新数据（刷新出自增 id、默认时间等字段）
    return favorite       # 返回完整的收藏对象（含 id）给上层使用


# 取消收藏：删除该用户对某条新闻的收藏记录
async def remove_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    # 构造 DELETE 语句：按 用户id + 新闻id 两个条件精确删除（防止误删别人的收藏）
    stmt = delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)  # 执行删除
    await db.commit()                # 提交事务 → 删除真正生效
    # result.rowcount：本次操作影响的行数
    # > 0 → 确实删掉了记录 → 返回 True；= 0 → 本来就没收藏 → 返回 False
    return result.rowcount > 0


# ------- 关键区别：添加收藏 vs 取消收藏 -------
# 数据库操作   INSERT（插入）      DELETE（删除）
# 用什么      db.add(favorite)   delete(Favorite)
# 针对对象     新建的对象        已存在的记录

# 为什么必须连表查询：
# 收藏表里只有"谁收藏了哪条新闻"的 id，没有新闻的标题、封面、简介等展示信息，
# 而"收藏列表"接口要给前端返回完整的新闻内容，所以必须去新闻表把对应记录一起取出来
# 两张表：
#   收藏表 favorite（记录"谁收藏了哪条新闻"）
#   新闻表 news（存放新闻的标题、封面、简介等详情）
# 靠一个条件连：favorite.news_id == news.id
# 获取收藏列表：获取的是某个用户的收藏列表 + 分页功能
async def get_favorite_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,        # 当前页码（默认第1页）
        page_size: int = 10   # 每页条数（默认10条）
):
    # 第1步：查总量（该用户收藏了多少条，用于前端计算总页数）
    count_query = select(func.count()).where(Favorite.user_id == user_id)  # SELECT COUNT(*) FROM favorite WHERE user_id=?
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()  # 取出唯一的数字 → 收藏总数

    # 第2步：获取收藏列表 - 联表查询 join() + 收藏时间排序 + 分页
    # 语法：select(查询主体模型类, 字段别名).join(联合查询的模型类, 联合查询的条件).where().order_by().offset().limit()
    # label("别名")：给字段起别名，方便后面用属性名取到对应值
    offset = (page - 1) * page_size  # 计算跳过条数（第2页 → 跳过前10条）
    # 查询结果每行结构：
    # [
    #   (新闻对象, 收藏时间, 收藏id)   ← 每行是一个元组
    # ]
    query = (select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id"))  # 查新闻 + 收藏时间 + 收藏id
             .join(Favorite, Favorite.news_id == News.id)   # 联表：收藏表.news_id = 新闻表.id
             .where(Favorite.user_id == user_id)            # 条件：该用户的收藏
             .order_by(Favorite.created_at.desc())          # 排序：按收藏时间倒序（最新在前，desc()降序）
             .offset(offset).limit(page_size)               # 分页：跳过 offset 条，取 page_size 条
             )
    result = await db.execute(query)
    rows = result.all()  # 取出所有行 → 列表，每个元素是一个元组(新闻对象, 收藏时间, 收藏id)
    return rows, total   # 返回两个值：当前页的列表 + 总条数（供路由分页响应）


# 清空收藏列表：删除当前用户的全部收藏记录
async def remove_all_favorites(
        db: AsyncSession,
        user_id: int
):
    # 构造 DELETE 语句：只按用户id删除（不限定新闻id，所以会删掉该用户所有收藏）
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)  # 执行删除
    await db.commit()                # 提交事务 → 生效

    # 返回删除的数量（result 是语句执行返回的结果对象；rowcount 可能为 0，用 or 0 兜底，避免返回 None）
    return result.rowcount or 0
