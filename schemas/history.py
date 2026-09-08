# ============================================================
# schemas 层：history.py —— 历史记录模块请求/响应模型
# 职责：参数校验 + 响应数据格式化（驼峰命名给前端）
# ============================================================

from datetime import datetime  # 时间类型（浏览时间字段）

from pydantic import BaseModel, Field, ConfigDict  # Pydantic：模型基类 / 字段定义 / 模型配置

from schemas.base import NewsItemBase  # 复用新闻项基础模型


class HistoryAddRequest(BaseModel):
    """
    添加历史记录请求
    """
    news_id: int = Field(..., alias="newsId")  # 前端字段名 newsId（... 必填）


class HistoryNewsItemResponse(NewsItemBase):
    """
    浏览历史列表中的新闻项响应
    """
    history_id: int = Field(alias="historyId")    # 历史记录id（前端字段名 historyId）
    view_time: datetime = Field(alias="viewTime") # 浏览时间（前端字段名 viewTime）

    model_config = ConfigDict(
        populate_by_name=True,  # 允许别名和字段名兼容
        from_attributes=True)   # 允许从 ORM 对象取值


class HistoryListResponse(BaseModel):
    """历史列表接口响应：list + total + hasMore"""
    list: list[HistoryNewsItemResponse]  # 历史新闻列表
    total: int                           # 总数（分页用）
    has_more: bool = Field(alias="hasMore")  # 是否还有更多（前端字段名 hasMore）

    model_config = ConfigDict(
        populate_by_name=True,  # 允许别名和字段名兼容
        from_attributes=True    # 允许从 ORM 对象取值
    )