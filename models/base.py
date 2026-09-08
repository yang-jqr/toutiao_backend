# ============================================================
# models 层：base.py —— 统一 ORM 基类
# 目的：所有模型共享同一个 Base，使 Base.metadata.create_all 能一次建出全部表
# ============================================================
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
