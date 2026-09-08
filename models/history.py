# ============================================================
# models 层：history.py —— 浏览历史表 ORM 模型
# 职责：用 Python 类描述数据库表结构，SQLAlchemy 据此建表/查数据
# ============================================================

# 导入 SQLAlchemy 类型：ORM字段标注 / 字段定义 / 基类 / 整型 / 时间 / 外键 / 索引
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, ForeignKey, Index
from datetime import datetime  # 时间类型（浏览时间字段）
from models.base import Base  # 统一 ORM 基类
from models.users import User  # 用户模型（外键关联）
from models.news import News   # 新闻模型（外键关联）


class History(Base):
    """
    浏览历史表ORM模型
    """
    __tablename__ = 'history'  # 对应数据库表名

    # 创建索引（提升查询速度）
    __table_args__ = (
        Index('fk_history_user_idx', 'user_id'),    # 用户id索引
        Index('fk_history_news_idx', 'news_id'),    # 新闻id索引
        Index('idx_view_time', 'view_time'),        # 浏览时间索引（按时间排序/查询）
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="历史ID")  # 主键自增
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False, comment="用户ID")  # 外键→用户表
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey(News.id), nullable=False, comment="新闻ID")  # 外键→新闻表
    view_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="浏览时间")  # 浏览时间，默认当前时间


    def __repr__(self):  # 调试时打印友好格式
        return f"<History(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, view_time={self.view_time})>"
