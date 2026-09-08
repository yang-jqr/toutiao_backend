# ============================================================
# 路由层：users.py —— 用户模块接口
# 职责：接收请求 → 调用 crud 层处理 → 返回统一响应
# 接口：注册 / 登录 / 获取信息 / 更新信息 / 修改密码
# ============================================================

# 导入需要用到的类
from fastapi import APIRouter, Depends, HTTPException   # APIRouter路由 / Depends依赖注入 / HTTPException异常
from sqlalchemy.ext.asyncio import AsyncSession         # 异步会话类型（类型标注用）
from starlette import status                            # HTTP 状态码常量

from models.users import User                           # 用户模型（标注当前登录用户类型）
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserChangePasswordRequest  # 请求/响应模型

from config.db_conf import get_db                       # 数据库会话依赖
from crud import users                                  # crud 层：用户的数据库操作
from utils.response import success_response             # 统一成功响应格式
from utils.auth import get_current_user                 # 依赖项：验证 Token 返回当前用户

# 创建路由实例：前缀 /api/user，文档分组 users
router = APIRouter(prefix="/api/user", tags=["users"])


# ============================================================
# 接口1：用户注册  POST /api/user/register
# 流程：查重（用户名是否已存在）→ 创建用户 → 生成 Token → 返回
# ============================================================
@router.post("/register")
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)):  # 用户信息 和 db
    # 注册逻辑：验证用户是否存在 -> 创建用户 → 生成 Token  → 响应结果
    existing_user = await users.get_user_by_username(db, user_data.username)  # 第一步：查重
    if existing_user:                                    # 用户名已存在
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")  # 400：客户端请求有问题
    user = await users.create_user(db, user_data)        # 第二步：创建用户（密码加密后入库）
    token = await users.create_token(db, user.id)        # 第三步：生成 Token（注册后直接登录）
    # 期望返回的结构：
    # return {
    #   "code": 200,
    #   "message": "注册成功",
    #   "data": {
    #     "token": token,
    #     "userInfo": {
    #       "id": user.id,
    #       "username": user.username,
    #       "bio": user.bio,
    #       "avatar": user.avatar
    #     }
    #   }
    # }
    # 第四步：用 Pydantic 模型统一格式化响应
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功", data=response_data)  # 统一响应


# ============================================================
# 接口2：用户登录  POST /api/user/login
# 流程：验证用户名密码 → 生成 Token → 返回
# ============================================================
@router.post("/login")
async def login(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    # 登录逻辑：验证用户是否存在 -> 验证密码 -> 生成 Token  → 响应结果
    user = await users.authenticate_user(db, user_data.username, user_data.password)  # 验证用户名+密码
    if not user:                                        # 验证失败（用户不存在或密码错误）
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")  # 401：未认证
    token = await users.create_token(db, user.id)       # 验证通过 → 生成新 Token
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="登录成功啦", data=response_data)


# 查Token查用户 → 封装crud → 功能整合成一个工具函数 → 路由导入使用: 依赖注入
# 依赖注入 get_current_user：从请求头 Authorization 取 Token → 查库验证 → 返回当前用户；无效/过期自动抛 401
# ============================================================
# 接口3：获取当前用户信息  GET /api/user/info
# ============================================================
@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):  # 直接注入当前用户，无需自己写验证
    return success_response(message="获取用户信息成功", data=UserInfoResponse.model_validate(user))


# 修改用户信息：验证Token → 更新（用户输入数据 put 提交 → 请求体参数 → 定义Pydantic模型类） → 响应结果
# 参数：用户输入的 + 验证Token的 + db（调用更新的方法）
# ============================================================
# 接口4：修改用户信息  PUT /api/user/update
# ============================================================
@router.put("/update")
async def update_user_info(user_data: UserUpdateRequest, user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):  # 请求体 + 当前用户 + 数据库会话
    user = await users.update_user(db, user.username, user_data)  # 调用 crud 更新：只更新前端传的字段
    return success_response(message="更新用户信息成功", data=UserInfoResponse.model_validate(user))


# ============================================================
# 接口5：修改密码  PUT /api/user/password
# 请求体：{"oldPassword": "xx", "newPassword": "xx"}
# ============================================================
@router.put("/password")
async def update_password(
        password_data: UserChangePasswordRequest,       # 请求体：旧密码+新密码（Pydantic 校验）
        user: User = Depends(get_current_user),         # 当前登录用户
        db: AsyncSession = Depends(get_db)):            # 数据库会话
    # 调用 crud：校验旧密码 → 新密码加密 → 更新；返回 True/False
    res_change_pwd = await users.change_password(db, user, password_data.old_password, password_data.new_password)
    if not res_change_pwd:                              # 旧密码验证失败
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="修改密码失败，请稍后再试")
    return success_response(message="修改密码成功")       # 成功 → 无需返回数据
