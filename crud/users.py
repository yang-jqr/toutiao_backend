# ============================================================
# crud 层：users.py —— 用户模块的数据库操作
# 职责：封装所有对用户表/令牌表的增删改查，供路由层调用
# ============================================================

import uuid  # 生成唯一 Token（随机字符串）
from datetime import datetime, timedelta  # 时间处理：计算 Token 过期时间

from fastapi import HTTPException  # 抛异常
from sqlalchemy import select, update  # select 查询 / update 更新
from sqlalchemy.ext.asyncio import AsyncSession  # 异步会话类型（类型标注用）

from models.users import User, UserToken  # 导入模型类：用户、用户令牌
from schemas.users import UserRequest, UserUpdateRequest  # 请求体模型
from utils import security  # 密码加密/验证工具


# 根据用户名查询数据库
async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)  # SELECT * FROM user WHERE username=?
    result = await db.execute(query)
    return result.scalar_one_or_none()  # 最多一条；查不到返回 None


# 创建用户（密码加密后入库）
async def create_user(db: AsyncSession, user_data: UserRequest):
    # 先密码加密处理 → add
    hashed_password = security.get_hash_password(user_data.password)  # 密码加密（bcrypt）
    user = User(username=user_data.username, password=hashed_password)  # 创建用户对象
    db.add(user)              # 登记到会话
    await db.commit()         # 写入数据库
    await db.refresh(user)  # 从数据库读回最新的 user（拿到自增id等）
    return user


# 生成 Token（登录态凭证）
async def create_token(db: AsyncSession, user_id: int):
    # 生成 Token + 设置过期时间 → 查询数据库当前用户是否有 Token → 有：更新；没有：添加
    token = str(uuid.uuid4())  # 生成随机 UUID 作为 Token
    # timedelta(days=7, hours=2, minutes=30, seconds=10)  # 过期时间可自定义
    expires_at = datetime.now() + timedelta(days=7)  # 过期时间：7天后
    query = select(UserToken).where(UserToken.user_id == user_id)  # 查该用户是否已有 Token
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()

    if user_token:  # 已有 Token → 更新（重新登录时刷新）
        user_token.token = token
        user_token.expires_at = expires_at
    else:  # 没有 Token → 新增一条
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
        await db.commit()

    return token  # 把 Token 返回给前端


# 验证用户名和密码（登录用）
async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)  # 先查用户
    if not user:  # 用户不存在
        return None
    if not security.verify_password(password, user.password):  # 密码比对（明文 vs 密文）
        return None

    return user  # 验证通过 → 返回用户


# 根据 Token 查询用户：验证 Token → 查询用户
async def get_user_by_token(db: AsyncSession, token: str):
    query = select(UserToken).where(UserToken.token == token)  # 按 Token 查记录
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()

    if not db_token or db_token.expires_at < datetime.now():  # Token 不存在 或 已过期
        return None

    query = select(User).where(User.id == db_token.user_id)  # 再按 user_id 查用户
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 更新用户信息: update更新 → 检查是否命中 → 获取更新后的用户返回
async def update_user(db: AsyncSession, username: str, user_data: UserUpdateRequest):
    # update(User).where(User.username == username).values(字段=值, 字段=值)
    # user_data 是一个Pydantic类型，得到字典 → ** 解包
    # 没有设置值的不更新（model_dump 把 pydantic 转成字典，exclude_unset 排除未设置的字段，exclude_none 排除为 None 的字段）
    query = update(User).where(User.username == username).values(**user_data.model_dump(
        exclude_unset=True,  # 排除未设置的字段
        exclude_none=True    # 排除为 None 的字段
    ))
    result = await db.execute(query)
    await db.commit()

    # 检查更新：受影响行数为 0 → 用户不存在
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取一下更新后的用户
    updated_user = await get_user_by_username(db, username)
    return updated_user


# 修改密码: 验证旧密码 → 新密码加密 → 修改密码
async def change_password(db: AsyncSession, user: User, old_password: str, new_password: str):
    if not security.verify_password(old_password, user.password):  # 旧密码不对 → 返回 False
        return False

    hashed_new_pwd = security.get_hash_password(new_password)  # 新密码加密
    user.password = hashed_new_pwd  # 更新内存中对象的密码
    # 更新: 由SQLAlchemy真正接管这个 User 对象，确保可以 commit
    # 规避 session 过期或关闭导致的不能提交的问题
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True  # 修改成功
