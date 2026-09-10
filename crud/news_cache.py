# ============================================================
# crud 层：news_cache.py —— 新闻模块的数据库操作（带 Redis 缓存）
# 核心模式：缓存优先（Cache-Aside）→ 先查缓存，没命中再查库并写回缓存
# 好处：减少数据库压力，加快响应速度
# ============================================================

from fastapi.encoders import jsonable_encoder  # 把 ORM/Pydantic 对象转成普通字典
from sqlalchemy import select, func, update     # select 查询 / func SQL函数 / update 更新
from sqlalchemy.ext.asyncio import AsyncSession # 异步会话类型（类型标注用）

from cache.news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list, \
    get_cached_news_detail, cache_news_detail, get_cached_related_news, cache_related_news  # 缓存读写方法
from models.news import Category, News           # 模型类：分类、新闻
from schemas.base import NewsItemBase            # 新闻项基础响应模型
from schemas.news import NewsDetailResponse, RelatedNewsResponse  # 新闻详情/相关新闻响应模型


# 查询所有新闻分类（带缓存）
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 先尝试从缓存中获取数据
    cached_categories = await get_cached_categories()
    if cached_categories:  # 缓存命中 → 直接返回（不用查库）
        return cached_categories

    # 缓存未命中 → 查数据库
    # 查完必须回填缓存，下次同样的请求才能直接命中（这就是 Cache-Aside 的"回填"环节）
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()  # ORM

    # 写入缓存（下次请求直接命中）
    if categories:
        # 只有真查到数据才回填：空结果不写缓存，避免把"查不到"也缓存住
        categories = jsonable_encoder(categories)  # ORM 转成可序列化数据(dict)
        # jsonable_encoder:复杂对象变成json可以认识格式
        await set_cache_categories(categories)

    # 返回数据
    return categories  #之后 改路由 因为文件变了new_cache

# 分类：数据简单（id、名称、排序等），没有 datetime 等复杂类型，dict 完全够用；路由也不做 Pydantic 规范化 → dict 最省事。
# 新闻列表：字段复杂（有 publish_time 时间类型），代码演示了"统一返回 ORM"的写法 → ORM。
# 查询新闻列表（带缓存 + 分页）
async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    # 先尝试从缓存获取新闻列表
    # 跳过的数量skip = (页码 -1) * 每页数量 → 页码 = 跳过的数量 // 每页数量 + 1
    # await get_cache_news_list(分类id, 页码, 每页数量)
    page = skip // limit + 1  # 由 skip 反推页码（缓存 key 需要页码）
    cached_list = await get_cache_news_list(category_id, page, limit)  # 缓存数据 json
    if cached_list:  # 缓存命中
        # return cached_list  # 要的是 ORM
        return [News(**item) for item in cached_list]  # 把字典列表还原成 News ORM 对象
    # **item：字典解包 → News(**item) = News(id=item['id'], title=item['title'], ...)
    # 缓存未命中 → 查数据库
    # 查询的是指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_list = result.scalars().all()

    # 写入缓存
    if news_list:
        # 只有查到数据才回填缓存（空列表不写缓存）
        # 先把 ORM 数据 转换 字典才能写入缓存
        # ORM 转成 Pydantic，再转为 字典  更严谨想要哪个选哪个
        # by_alias=False 不适用别名，保存 Python 风格，因为 Redis 数据是给后端用的
        #jsonable_encoder:复杂对象变成json可以认识格式 也可以转换
        #news_list = jsonable_encoder(news_list)  # ORM → dict
        # ORM → Pydantic → dict
        news_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in news_list]
        await set_cache_news_list(category_id, page, limit, news_data)

    return news_list

# 对比总结
# get_categories	get_news_list
# 缓存命中返回	dict（直接）	ORM（还原）
# 缓存未命中返回	dict（jsonable_encoder 转了）	ORM（没转）
# 统一类型	dict	ORM
# 本质	简单数据，dict 够用	演示"crud 返回 ORM"的约定


# 查询指定分类下的新闻数量（用于分页总量，数量变化频繁，不缓存）
async def get_news_count(db: AsyncSession, category_id: int):
    # 查询的是指定分类下的新闻数量
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()  # 只能有一个结果，否则报错


# 查询单条新闻详情（带缓存）
async def get_news_detail(db: AsyncSession, news_id: int):
    # 先尝试从缓存获取
    cached_news = await get_cached_news_detail(news_id)
    if cached_news:  # 缓存命中
        # 缓存数据可能包含 related_news，需要过滤掉（News 模型没有这个字段）
        # filtered_data = {k: v for k, v in cached_news.items() if k != 'related_news'}
        # return News(**filtered_data)
        return News(**cached_news)  # 字典 → News ORM 对象

    # 缓存未命中 → 查数据库
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()

    # 如果查询到数据，存入缓存（不使用别名，保持数据库字段名）
    if news:
        # 未命中后的回填：下次同一个 news_id 就能直接命中缓存
        # 构造新闻详情数据用于缓存（包含 content 字段）
        # news_dict = {k: v for k, v in news.__dict__.items() if not k.startswith('_')}
        news_dict = NewsDetailResponse.model_validate(news).model_dump(  # ORM → 字典
            by_alias=False, mode="json", exclude={'related_news'}  # 排除相关新闻字段（单独缓存）
        )
        await cache_news_detail(news_id, news_dict)  # 写入详情缓存

    return news


# 浏览量 +1（写操作，实时更新，不缓存）
async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)  # SQL 原子自增
    result = await db.execute(stmt)
    await db.commit()

    # 更新 → 检查数据库是否真的命中了数据 → 命中了返回True
    return result.rowcount > 0


# 查询相关新闻（带缓存）
async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    cached_related = await get_cached_related_news(news_id, category_id)  # 先查缓存
    if cached_related:  # 缓存命中
        # 缓存数据是字典列表，直接返回
        return cached_related
    # 缓存未命中 → 查数据库
    # order_by 排序 → 浏览量和发布时间
    stmt = select(News).where(
        News.category_id == category_id,  # 条件1：同一分类
        News.id != news_id                # 条件2：不是当前新闻
    ).order_by(
        News.views.desc(),  # 默认是升序，desc 表示降序（最热在前）
        News.publish_time.desc()  # 浏览量相同再按时间倒序
    ).limit(limit)
    result = await db.execute(stmt)
    # return result.scalars().all()
    related_news = result.scalars().all()

    # 转换为字典格式用于缓存和返回（不使用别名，保持数据库字段名）
    if related_news:
        # 未命中后的回填：上次查库的结果存进缓存，下次同 id+分类直接命中
        related_data = [
            RelatedNewsResponse.model_validate(news).model_dump(by_alias=False, mode="json")
            for news in related_news
        ]
        await cache_related_news(news_id, category_id, related_data)  # 写入相关新闻缓存
        return related_data

    # 没有相关新闻，返回空列表
    return []  # 查库也没结果 → 直接返回空列表（空结果不缓存，免得把"没有"缓存住）
    # 列表推导式 推导出新闻的核心数据，然后再 return
    # return [{
    #     "id": news_detail.id,
    #     "title": news_detail.title,
    #     "content": news_detail.content,
    #     "image": news_detail.image,
    #     "author": news_detail.author,
    #     "publishTime": news_detail.publish_time,
    #     "categoryId": news_detail.category_id,
    #     "views": news_detail.views
    # } for news_detail in related_news]
