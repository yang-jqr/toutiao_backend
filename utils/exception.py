# ============================================================
# utils 层：exception.py —— 异常处理器（具体实现）
# 职责：把各类异常统一转成 {code, message, data} 格式返回给前端
# ============================================================

import traceback  # 格式化异常堆栈（调试用）

from fastapi import HTTPException, Request  # HTTP异常 / 请求对象
from fastapi.responses import JSONResponse  # JSON 响应
from sqlalchemy.exc import IntegrityError, SQLAlchemyError  # 数据库异常类型
from starlette import status  # HTTP 状态码常量

# 开发模式：返回详细错误信息
# 生产模式：返回简化错误信息
DEBUG_MODE = True  # 教学项目保持开启


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    处理 HTTPException 异常（业务逻辑主动抛出的异常）
    """
    # HTTPException 通常是业务逻辑主动抛出的，data 保持 None
    return JSONResponse(
        status_code=exc.status_code,  # 使用异常自带的状态码（如 400/401/404）
        content={
            "code": exc.status_code,  # 业务状态码 = HTTP 状态码
            "message": exc.detail,    # 错误提示信息
            "data": None
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    处理数据库完整性约束错误（如：用户名重复、外键不存在）
    """
    error_msg = str(exc.orig)  # 取出数据库原始错误信息

    # 判断具体的约束错误类型
    if "username_UNIQUE" in error_msg or "Duplicate entry" in error_msg:
        detail = "用户名已存在"          # 唯一约束冲突 → 用户名重复
    elif "FOREIGN KEY" in error_msg:
        detail = "关联数据不存在"        # 外键约束 → 关联的记录不存在
    else:
        detail = "数据约束冲突，请检查输入"  # 其它约束

    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": "IntegrityError",   # 错误类型
            "error_detail": error_msg,        # 原始错误详情
            "path": str(request.url)          # 请求路径
        }

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,  # 统一返回 400（客户端请求问题）
        content={
            "code": 400,
            "message": detail,
            "data": error_data
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """
    处理 SQLAlchemy 数据库错误（SQL 语法错、连接失败等）
    """
    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,     # 异常类型名
            "error_detail": str(exc),             # 异常详情
            # 格式化异常信息为字符串，方便日志记录和调试
            "traceback": traceback.format_exc(),  # 堆栈信息
            "path": str(request.url)              # 请求路径
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # 500：服务端错误
        content={
            "code": 500,
            "message": "数据库操作失败，请稍后重试",
            "data": error_data
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    处理所有未捕获的异常（兜底）
    """
    # 开发模式下返回详细错误信息
    error_data = None
    if DEBUG_MODE:
        error_data = {
            "error_type": type(exc).__name__,     # 异常类型名
            "error_detail": str(exc),             # 异常详情
            # 格式化异常信息为字符串，方便日志记录和调试
            "traceback": traceback.format_exc(),  # 堆栈信息
            "path": str(request.url)              # 请求路径
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # 500：服务端错误
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": error_data
        }
    )



