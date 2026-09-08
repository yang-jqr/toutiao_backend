# ============================================================
# utils 层：exception_handlers.py —— 异常处理器注册
# 职责：把各类异常处理器注册到 FastAPI 应用上
# ============================================================

from fastapi import HTTPException  # HTTP 异常
from sqlalchemy.exc import IntegrityError, SQLAlchemyError  # 数据库异常类型

from utils.exception import http_exception_handler, integrity_error_handler, sqlalchemy_error_handler, \
    general_exception_handler  # 导入各个异常处理函数


def register_exception_handlers(app):
    """
    注册全局异常处理：子类在前，父类在后；具体在前，抽象在后
    """
    app.add_exception_handler(HTTPException, http_exception_handler)  # 业务异常（最具体）
    app.add_exception_handler(IntegrityError, integrity_error_handler)  # 数据完整性约束
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)  # 数据库异常（父类）
    app.add_exception_handler(Exception, general_exception_handler)  # 兜底（所有未捕获异常）
