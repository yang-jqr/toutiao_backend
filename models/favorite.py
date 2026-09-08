# ============================================================
# models 层：favorite.py —— 收藏表 ORM 模型
# 职责：用 Python 类描述数据库表结构，SQLAlchemy 据此建表/查数据
# ============================================================

from datetime import datetime  # 时间类型（收藏时间字段）

# 导入 SQLAlchemy 类型和约束：唯一约束 / 索引 / 整型 / 外键 / 时间
from sqlalchemy import UniqueConstraint, Index, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column  # 类型标注 / 字段定义

from models.base import Base  # 统一 ORM 基类
from models.news import News  # 新闻模型（外键关联）
from models.users import User  # 用户模型（外键关联）


class Favorite(Base):
    """
    收藏表ORM模型
    """
    __tablename__ = 'favorite'  # 对应数据库表名

    # 创建索引
    # UniqueConstraint: 唯一约束, 当前用户，当前新闻，只能收藏一次
    __table_args__ = (
        UniqueConstraint('user_id', 'news_id', name='user_news_unique'),  # 同一用户同一新闻不能重复收藏
        Index('fk_favorite_user_idx', 'user_id'),  # 用户id索引：加快按用户查询
        Index('fk_favorite_news_idx', 'news_id'),  # 新闻id索引：加快按新闻查询
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="收藏ID")  # 主键自增
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False, comment="用户ID")  # 外键→用户表
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey(News.id), nullable=False, comment="新闻ID")  # 外键→新闻表
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, comment="收藏时间")  # 收藏时间，默认当前时间

    def __repr__(self):  # 调试时打印友好格式
        return f"<Favorite(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, created_at={self.created_at})>"
