# ============================================================
# schemas 层：news.py —— 新闻详情/相关新闻 响应模型
# 本文件存放新闻模块的 Pydantic 模型（请求体校验 / 响应序列化）：
#   RelatedNewsResponse —— 相关新闻简化项（只要 id/title/image/views）
#   NewsDetailResponse  —— 新闻详情响应，继承 NewsItemBase 再加 content / relatedNews
# 职责：参数校验 + 响应数据格式化（驼峰命名给前端）
# 用途：配合缓存，把 ORM 数据转成可序列化的字典存 Redis
# ============================================================

from typing import Optional  # 可选类型

from pydantic import Field, ConfigDict, BaseModel  # Pydantic：模型基类 / 字段定义 / 模型配置

from schemas.base import NewsItemBase  # 复用新闻项基础模型


class RelatedNewsResponse(BaseModel):
    """
    相关新闻响应（简化版，只包含必要字段）
    """
    id: int                    # 新闻ID
    title: str                 # 标题
    image: Optional[str] = None  # 封面图（可空）
    views: int                 # 浏览量

    model_config = ConfigDict(
        from_attributes=True,  # 允许从 ORM 对象取值
    )


class NewsDetailResponse(NewsItemBase):
    """
    新闻详情响应（继承自 NewsItemResponse，新增 content 和 related_news）
    """
    content: str  # 新增：新闻内容
    related_news: list[RelatedNewsResponse] = Field(default_factory=list, alias="relatedNews")  # 新增相关新闻（默认空列表）

    model_config = ConfigDict(
        populate_by_name=True,  # 允许别名和字段名兼容
        from_attributes=True    # 允许从 ORM 对象取值
    )




