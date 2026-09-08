# ============================================================
# models 层：users.py —— 用户表 + 用户令牌表 ORM 模型
# 职责：用 Python 类描述数据库表结构，SQLAlchemy 据此建表/查数据
# ============================================================

from datetime import datetime  # 时间类型（创建/更新时间字段）
from typing import Optional    # 可选类型（允许为 NULL 的字段）

# 导入 SQLAlchemy 类型：索引 / 整型 / 字符串 / 枚举 / 时间 / 外键
from sqlalchemy import Index, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column  # 类型标注 / 字段定义

from models.base import Base  # 统一 ORM 基类


class User(Base):
    """
    用户信息表ORM模型
    """
    __tablename__ = 'user'  # 对应数据库表名

    # 创建索引
    __table_args__ = (
        Index('username_UNIQUE', 'username'),  # 用户名索引（配合唯一约束）
        Index('phone_UNIQUE', 'phone'),        # 手机号索引（配合唯一约束）
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")  # 主键自增
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名")  # 用户名（唯一）
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码（加密存储）")  # 密码密文
    nickname: Mapped[Optional[str]] = mapped_column(String(50), comment="昵称")  # 昵称（可空）
    avatar: Mapped[Optional[str]] = mapped_column(String(255), comment="头像URL",  # 头像（可空，有默认图）
                                                  default='https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg')
    gender: Mapped[Optional[str]] = mapped_column(Enum('male', 'female', 'unknown'), comment="性别", default='unknown')  # 性别枚举
    bio: Mapped[Optional[str]] = mapped_column(String(500), comment="个人简介", default='这个人很懒，什么都没留下')  # 简介（有默认）
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, comment="手机号")  # 手机号（唯一，可空）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), comment="创建时间")  # 创建时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), onupdate=datetime.now(),  # 更新时间（自动刷新）
                                                 comment="更新时间")


    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', nickname='{self.nickname}')>"


class UserToken(Base):
    """
    用户令牌表ORM模型（登录后生成，用于验证身份）
    """
    __tablename__ = 'user_token'  # 对应数据库表名

    # 创建索引
    __table_args__ = (
        Index('token_UNIQUE', 'token'),              # 令牌值索引（唯一）
        Index('fk_user_token_user_idx', 'user_id'),  # 用户id索引（按用户查令牌）
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="令牌ID")  # 主键自增
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False, comment="用户ID")  # 外键→用户表
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="令牌值")  # 令牌（唯一）
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")  # 过期时间（必填）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), comment="创建时间")  # 创建时间


    def __repr__(self):
        return f"<UserToken(id={self.id}, user_id={self.user_id}, token='{self.token}')>"