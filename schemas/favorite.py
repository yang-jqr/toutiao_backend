# ============================================================
# schemas 层：favorite.py —— 收藏模块请求/响应模型
# schemas 层的模型类（BaseModel 的子类）就是给接口数据定"模板/契约"的——规定"这个接口收的数据长什么样、返回的数据长什么样"。
# 它干两件大事：
# ① 请求校验（管"进"）：前端传进来的数据，模型类负责检查合不合格
# ② 响应格式化（管"出"）：数据库查出来的 ORM 对象/字典，模型类负责转成前端想要的 JSON（字段改名、裁剪、嵌套）
# 职责：参数校验 + 响应数据格式化（驼峰命名给前端）
# ============================================================

from datetime import datetime  # 时间类型（收藏时间字段）

from pydantic import BaseModel, Field, ConfigDict  # Pydantic：模型基类 / 字段定义 / 模型配置

from schemas.base import NewsItemBase  # 复用新闻项基础模型


# 检查收藏状态的响应模型：{"isFavorite": true/false}
class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(..., alias="isFavorite")  # 前端字段名 isFavorite（... 必填）


# 添加收藏的请求体模型：{"newsId": 1}
class FavoriteAddRequest(BaseModel):
    news_id: int = Field(..., alias="newsId")  # 前端字段名 newsId


# 收藏列表中的"新闻项"模型：新闻字段 + 收藏信息
# 规划两个类： 一个是新闻模型类 + 收藏的模型类
class FavoriteNewsItemResponse(NewsItemBase):  # 继承 NewsItemBase（新闻公共字段）
    favorite_id: int = Field(alias="favoriteId")      # 收藏记录id（前端字段名 favoriteId）
    favorite_time: datetime = Field(alias="favoriteTime")  # 收藏时间（前端字段名 favoriteTime）

    model_config = ConfigDict(
        populate_by_name=True,  # 允许别名和字段名兼容
        from_attributes=True    # 允许从 ORM 对象取值
    )


# 收藏列表接口响应模型类：list + total + hasMore
class FavoriteListResponse(BaseModel):
    list: list[FavoriteNewsItemResponse]  # 收藏新闻列表
    total: int                            # 收藏总数（分页用）
    has_more: bool = Field(alias="hasMore")  # 是否还有更多（前端字段名 hasMore）

    model_config = ConfigDict(
        populate_by_name=True,  # 允许别名和字段名兼容
        from_attributes=True    # 允许从 ORM 对象取值
    )
