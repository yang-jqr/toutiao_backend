# ============================================================
# utils 层：auth.py —— 身份认证工具
# 职责：从请求头提取 Token → 验证 → 返回当前用户（供路由依赖注入）
# ============================================================

from fastapi import Header, Depends, HTTPException  # Header请求头 / Depends依赖注入 / HTTPException异常
from sqlalchemy.ext.asyncio import AsyncSession     # 异步会话类型（类型标注用）
from starlette import status                        # HTTP 状态码常量

from config.db_conf import get_db   # 数据库会话依赖
from crud import users              # 用户 crud 操作


# 整合 根据 Token 查询用户，返回用户（作为依赖项注入到路由）
async def get_current_user(
        authorization: str = Header(..., alias="Authorization"),  # 从请求头取 Authorization 字段（... 必填）
        # get_current_user 的核心工作是用 Token 去数据库查用户，而查数据库必须先拿到一个数据库会话(db)，
        # 所以必须有一个参数来接收它
        db: AsyncSession = Depends(get_db)                        # 依赖注入数据库会话
):
    # 前端请求头格式：Authorization: Bearer xxxxx
    # token = authorization.split(" ")[1]   # 也可以这样切分
    token = authorization.replace("Bearer ", "")  # 去掉 "Bearer " 前缀，拿到真正的 Token
    user = await users.get_user_by_token(db, token)  # 查库验证 Token → 返回用户
    if not user:  # Token 无效或已过期
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌或已经过期的令牌")

    return user  # 验证通过 → 把用户对象交给路由使用
