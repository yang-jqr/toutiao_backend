# ============================================================
# cache 层：news_cache.py —— 新闻缓存方法  
# 职责：封装新闻数据的缓存 key 规则 + 读取/写入（基于 Redis）
# 缓存层:缓存模式：先查缓存 → 有则直接返回；没有则查库 → 再写回缓存
# ============================================================

# 新闻相关的缓存方法：新闻分类的读取和写入
# key - value
from typing import List, Dict, Any, Optional  # 类型标注：列表/字典/任意/可选

from config.cache_conf import get_json_cache, set_cache  # 引入 Redis 底层读写方法

# 缓存 key 规则（用冒号分层，方便管理）
CATEGORIES_KEY = "news:categories"        # 分类缓存固定 key
NEWS_LIST_PREFIX = "news_list:"           # 新闻列表前缀 → news_list:分类:页码:每页条数
NEWS_DETAIL_PREFIX = "news:detail:"       # 新闻详情前缀 → news:detail:新闻id
RELATED_NEWS_PREFIX = "news:related:"     # 相关新闻前缀 → news:related:新闻id:分类id

#新闻分类
# 获取新闻分类缓存（读）
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)


# 写入新闻分类缓存: 缓存的数据, 过期时间（写）
# 分类、配置 7200；列表： 600； 详情： 1800；验证码：120 -- 数据越稳定，缓存越持久
# 避免所有key同时过期 引起缓存雪崩（错开过期时间）
async def set_cache_categories(data: List[Dict[str, Any]], expire: int = 7200):
    return await set_cache(CATEGORIES_KEY, data, expire)



#新闻列表
# 写入缓存-新闻列表 key = news_list:分类id:页码:每页数量  + 列表数据 + 过期时间（写）
async def set_cache_news_list(category_id: Optional[int], page: int, size: int, news_list: List[Dict[str, Any]], expire: int = 1800):
    # 调用 封装的 Redis 的设置方法，存新闻列表到缓存
    category_part = category_id if category_id is not None else "all"  # 无分类时用 "all"
    key = f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"  # f""拼接唯一key 分类id分情况
    return await set_cache(key, news_list, expire)


# 读取缓存-新闻列表（读）→ key 规则必须和写入时一致才能命中
async def get_cache_news_list(category_id: Optional[int], page: int, size: int):
    category_part = category_id if category_id is not None else "all"
    key = f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"
    return await get_json_cache(key)


# 获取缓存的新闻详情（读）
async def get_cached_news_detail(news_id: int) -> Optional[Dict[str, Any]]:
    """
    获取缓存的新闻详情

    Args:
        news_id: 新闻ID

    Returns:
        Optional[Dict[str, Any]]: 新闻数据，不存在则返回None
    """
    key = f"{NEWS_DETAIL_PREFIX}{news_id}"  # 每个新闻一个 key
    return await get_json_cache(key)


# 缓存新闻详情（写），默认过期 5 分钟
async def cache_news_detail(news_id: int, news_data: Dict[str, Any], expire: int = 300) -> bool:
    """
    缓存新闻详情

    Args:
        news_id: 新闻ID
        news_data: 新闻数据字典
        expire: 过期时间（秒），默认5分钟

    Returns:
        bool: 缓存成功返回True
    """
    key = f"{NEWS_DETAIL_PREFIX}{news_id}"
    return await set_cache(key, news_data, expire)


# 缓存相关新闻列表（写）
async def cache_related_news(news_id: int, category_id: int, related_list: List[Dict[str, Any]], expire: int = 1800) -> bool:
    """
    缓存相关新闻列表

    Args:
        news_id: 当前新闻ID
        category_id: 新闻分类ID
        related_list: 相关新闻列表数据
        expire: 过期时间（秒）

    Returns:
        bool: 缓存成功返回True
    """
    key = f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}"  # 新闻id+分类id 组合 key
    return await set_cache(key, related_list, expire)


# 获取缓存的相关新闻列表（读）
async def get_cached_related_news(news_id: int, category_id: int) -> Optional[List[Dict[str, Any]]]:
    """
    获取缓存的相关新闻列表

    Args:
        news_id: 当前新闻ID
        category_id: 新闻分类ID

    Returns:
        Optional[List[Dict[str, Any]]]: 相关新闻列表数据，不存在则返回None
    """
    key = f"{RELATED_NEWS_PREFIX}{news_id}:{category_id}"
    return await get_json_cache(key)