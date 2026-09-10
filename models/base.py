# ============================================================
# models 层：base.py —— 统一 ORM 基类
# 目的：所有模型共享同一个 Base，使 Base.metadata.create_all 能一次建出全部表
# ============================================================
# ORM 模型类三步套路：
# 1. 基类：继承 DeclarativeBase（本项目把基类收敛到本文件，各模型统一 import 这里的 Base）
# 2. 数据库表模型类：继承基类 Base
# 3. 属性及类型：参照数据库表定义
# 导入声明式基类：SQLAlchemy 2.0 声明式 ORM 的入口
from sqlalchemy.orm import DeclarativeBase


# 统一 ORM 基类：所有模型类都继承它（继承后才能用 Mapped / mapped_column 的类型标注写法）
# 注意：公共的时间字段（created_at / updated_at）没有放在这个基类里，而是由 Category / News 各自声明
#       各模型只要继承同一个 Base，Base.metadata.create_all 就能一次性建出全部表
class Base(DeclarativeBase):
    pass  # 空基类：本文件只负责提供统一的 Base，不定义任何字段
