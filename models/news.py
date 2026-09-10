# ============================================================
# models 层：news.py —— 新闻表 + 分类表 ORM 模型
# 职责：用 Python 类描述数据库表结构，SQLAlchemy 据此建表/查数据
# ============================================================

from datetime import datetime  # 时间类型（创建/更新时间字段）
from typing import Optional    # 可选类型（允许为 NULL 的字段），Optional[str] 等价于 str | None

from sqlalchemy import DateTime, Index, Text, ForeignKey  # 时间 / 索引 / 大文本 / 外键
from sqlalchemy.orm import Mapped, mapped_column  # 类型标注 / 字段定义
from sqlalchemy import Integer, String  # 整型 / 字符串

from models.base import Base  # 统一 ORM 基类（所有模型共享同一个 Base，create_all 才能一次建出全部表）


# 新闻分类表
class Category(Base):
    __tablename__ = "news_category"  # 对应数据库表名

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="分类ID")  # 主键：整数、自增
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="分类名称")  # 分类名：最长50字符、唯一、非空
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")  # 排序权重：整数、默认0、非空
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")  # default：插入时取当前时间；comment：写进数据库的字段注释
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")  # default：插入时取当前时间；onupdate：更新记录时自动刷新

    # __repr__：打印对象时显示的友好格式（方便调试）
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, sort_order={self.sort_order})>"


# 新闻表
class News(Base):
    __tablename__ = "news"  # 对应数据库表名

    # 创建索引：提升查询速度 → 添加目录
    __table_args__ = (
        Index('fk_news_category_idx', 'category_id'),  # 高频查询场景（按分类查新闻）
        Index('idx_publish_time', 'publish_time')  # 按发布时间排序
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")  # 主键：整数、自增
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="新闻标题")  # 标题：最长255字符、非空（必填）
    description: Mapped[Optional[str]] = mapped_column(String(500), comment="新闻简介")  # 简介：可空、最长500字符
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="新闻内容")  # 正文：Text 长文本类型、非空
    image: Mapped[Optional[str]] = mapped_column(String(255), comment="封面图片URL")  # 封面图URL：可空、最长255字符
    author: Mapped[Optional[str]] = mapped_column(String(50), comment="作者")  # 作者：可空、最长50字符
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('news_category.id'), nullable=False, comment="分类ID")  # 外键：关联 news_category 表的 id、非空
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="浏览量")  # 浏览量：整数、默认0、非空
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发布时间")  # 发布时间：日期时间、默认当前时间
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")  # default：插入时取当前时间；comment：写进数据库的字段注释
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")  # default：插入时取当前时间；onupdate：更新记录时自动刷新

    # __repr__：打印对象时显示的友好格式（方便调试）
    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title}', views={self.views})>"
