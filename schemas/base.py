# ============================================================
# schemas 层：base.py —— 新闻项基础响应模型
# 职责：定义"新闻项"的公共字段，收藏/历史等模块复用（继承）
# ============================================================

from datetime import datetime  # 时间类型（发布时间字段）
from typing import Optional    # 可选类型

from pydantic import BaseModel, Field, ConfigDict  # Pydantic：模型基类 / 字段定义 / 模型配置


class NewsItemBase(BaseModel):
    """新闻项基础模型：收藏列表、历史列表里的每条新闻都用它"""
    id: int                                                  # 新闻ID
    title: str                                               # 标题
    description: Optional[str] = None                        # 简介（可空）
    image: Optional[str] = None                              # 封面图（可空）
    author: Optional[str] = None                             # 作者（可空）
    category_id: int = Field(alias="categoryId")             # 分类ID（前端字段名是 categoryId）
    views: int                                               # 浏览量
    publish_time: Optional[datetime] = Field(None, alias="publishedTime")  # 发布时间（前端字段名 publishedTime）

    model_config = ConfigDict(          # 模型配置
        from_attributes=True,           # 允许从 ORM 对象属性取值
        populate_by_name=True           # 允许同时用别名和字段名传值
    )