# ============================================================
# 路由层：news.py —— 新闻模块接口（day06：带 Redis 缓存）
# 职责：接收请求 → 调用 crud 层处理 → 返回统一响应
# 注意：查询类接口走 news_cache（先查缓存），写操作走 news（直接操作数据库）
# ============================================================

# 导入需要用到的类
from fastapi import APIRouter, Depends, Query, HTTPException  # APIRouter路由 / Depends依赖注入 / Query查询参数校验 / HTTPException异常
from sqlalchemy.ext.asyncio import AsyncSession              # 异步会话类型（类型标注用）

from config.db_conf import get_db   # 数据库会话依赖
from crud import news               # crud 层：新闻的写操作（浏览量+1、计数）
from crud import news_cache         # crud 层：新闻的读操作（带缓存：分类/列表/详情/相关新闻）

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组 标签
router = APIRouter(prefix="/api/news", tags=["news"])  # 创建路由实例：所有接口加前缀 /api/news，文档中分组为 news

# 添加路由 → 定义模型类 → 封装 CRUD 方法 → 路由处理函数调用方法

# 接口实现流程（为什么要分层？一个模块一个文件，按模块划分路由）
# 一句话：一层只干一件事 —— 路由接请求、crud 查数据、models 定义表、config 连数据库
# 好处：好复用、好改、好测试
# 1. 模块化路由 → 先定好有哪些接口（API 接口规范文档，相当于给前端看的"菜单"）
# 2. 定义模型类 → 告诉 SQLAlchemy"数据库表长什么样"（数据库设计文档，没它就没法查数据）
# 3. crud 封装查询 → 所有查数据的 SQL 都放这里，接口直接调用，不用重复写（封装操作数据库的方法）
# 4. 路由调用 crud → 拿到数据，包装成统一格式（code/message/data）返回

# 路由就是 URL 地址和处理函数之间的映射关系，它决定了当用户访问某个特定网址时，服务器应该执行哪段代码来返回结果。


# ============================================================
# 接口1：获取新闻分类  GET /api/news/categories（走缓存）
# ============================================================
@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # 先获取数据库里面新闻分类数据 → 先定义模型类 → 封装查询数据的方法
    # 调用带缓存的 crud：先查 Redis，没命中再查库并写回缓存
    categories = await news_cache.get_categories(db, skip, limit)  # 调用 crud 层带缓存的查询方法（await 等待异步结果）
    # 统一响应格式（业务状态码约定）
    # code: 业务状态码，200 表示成功（注意：不是 HTTP 状态码）
    # message: 提示信息
    # data: 实际返回的数据
    return {                                          # 统一响应格式
        "code": 200,                                  # 业务状态码：成功
        "message": "获取新闻分类成功",                  # 提示信息
        "data": categories                            # 数据：分类列表
    }


# ============================================================
# 接口2：获取新闻列表  GET /api/news/list?categoryId=xx&page=1&pageSize=10（走缓存）
# ============================================================
@router.get("/list")
async def get_news_list(
        category_id: int = Query(..., alias="categoryId"),  # 必填查询参数（... 表示必填），前端参数名为 categoryId
        page: int = 1,                                      # 页码，默认第 1 页
        page_size: int = Query(10, alias="pageSize", le=100),  # 每页条数：前端参数名 pageSize，默认10，le=100 表示最大100（超出报 422）
        db: AsyncSession = Depends(get_db)                  # 依赖注入数据库会话
):
    # 思路：处理分页规则 → 查询新闻列表 → 计算总量 → 计算是否还有更多
    offset = (page - 1) * page_size                          # 计算 SQL 的 offset（跳过条数），如第2页每页10条则跳过10条
    news_list = await news_cache.get_news_list(db, category_id, offset, page_size)  # 带缓存的列表查询（当前页新闻列表）
    total = await news.get_news_count(db, category_id)       # 查询该分类下新闻总数（用于分页；数量频繁变化，不缓存）
    # (跳过的 + 当前列表里面的数量) < 总量 → 还有下一页
    has_more = (offset + len(news_list)) < total             # 已取到数量 < 总量，说明还有下一页
    return {                                                # 统一响应格式
        "code": 200,                                        # 业务状态码：成功
        "message": "获取新闻列表成功",                        # 提示信息
        "data": {                                           # 数据
            "list": news_list,                              # 当前页新闻列表
            "total": total,                                 # 新闻总数
            "hasMore": has_more                             # 是否还有更多（前端"加载更多"用）
        }
    }


# ============================================================
# 接口3：获取新闻详情  GET /api/news/detail?id=xx（详情/相关新闻走缓存）
# 流程：查详情(缓存) → 浏览量+1(实时) → 查相关新闻(缓存) → 返回
# ============================================================
@router.get("/detail")
async def get_news_detail(news_id: int = Query(..., alias="id"), db: AsyncSession = Depends(get_db)):
    # 获取新闻详情 + 浏览量+1 + 相关新闻
    news_detail = await news_cache.get_news_detail(db, news_id)  # 第一步：查询新闻详情（带缓存）
    if not news_detail:                                     # 如果查不到（返回 None）→ 404
        raise HTTPException(status_code=404, detail="新闻不存在")  # 抛 HTTP 404 异常，返回 {"detail": "新闻不存在"}

    views_res = await news.increase_news_views(db, news_detail.id)  # 第二步：浏览量+1（实时写库，不缓存）
    if not views_res:                                       # 如果更新没命中（rowcount 为 0，新闻可能被删）→ 双保险 404
        raise HTTPException(status_code=404, detail="新闻不存在")  # 同样抛 404（双保险）

    related_news = await news_cache.get_related_news(db, news_detail.id, news_detail.category_id)  # 第三步：查相关新闻（带缓存，同分类按热度排序）

    return {                                                # 统一响应格式
      "code": 200,                                          # 业务状态码：成功
      "message": "success",                                 # 提示信息
      "data": {                                             # 数据
        "id": news_detail.id,                               # 新闻ID
        "title": news_detail.title,                         # 标题
        "content": news_detail.content,                     # 正文
        "image": news_detail.image,                         # 封面图
        "author": news_detail.author,                       # 作者
        "publishTime": news_detail.publish_time,            # 发布时间（驼峰命名给前端）
        "categoryId": news_detail.category_id,              # 分类ID
        "views": news_detail.views,                         # 浏览量
        "relatedNews": related_news                         # 相关新闻列表
      }
    }
