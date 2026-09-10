# ============================================================
# 路由层：users.py —— 用户模块接口
# 职责：接收请求 → 调用 crud 层处理 → 返回统一响应
# 接口：注册 / 登录 / 获取信息 / 更新信息 / 修改密码
# ============================================================

# 导入需要用到的类
from fastapi import APIRouter, Depends, HTTPException   # APIRouter路由 / Depends依赖注入 / HTTPException异常
from sqlalchemy.ext.asyncio import AsyncSession         # 异步会话类型（类型标注用）
from starlette import status                            # 导入 HTTP 状态码常量（400/401/500 等，比手写数字更清晰）

from models.users import User                           # 用户模型（标注当前登录用户类型）
# 导入 Pydantic 请求/响应模型：参数校验 + 响应数据格式化
#   UserRequest                注册/登录请求体（username + password）
#   UserAuthResponse           登录/注册响应 data（token + userInfo）
#   UserInfoResponse           用户信息响应（id + username + 基础信息）
#   UserUpdateRequest          更新用户信息请求体
#   UserChangePasswordRequest   修改密码请求体（oldPassword + newPassword）
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserChangePasswordRequest  # 请求/响应模型

from config.db_conf import get_db                       # 数据库会话依赖
from crud import users                                  # crud 层：用户的数据库操作（查用户/建用户/生成Token等）
from utils.response import success_response             # 统一成功响应格式（code/message/data）
from utils.auth import get_current_user                 # 依赖项：根据 Token 验证身份，返回当前用户

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组 标签
router = APIRouter(prefix="/api/user", tags=["users"])  # 创建路由实例：所有接口加前缀 /api/user，文档中分组为 users


# ============================================================
# 接口1：用户注册  POST /api/user/register
# 流程：查重（用户名是否已存在）→ 创建用户 → 生成 Token → 返回
# ============================================================
@router.post("/register")
async def register(user_data: UserRequest, db: AsyncSession = Depends(get_db)):  # 用户信息 和 db
    # 注册逻辑：验证用户是否存在 -> 创建用户 → 生成 Token  → 响应结果
    existing_user = await users.get_user_by_username(db, user_data.username)  # 第一步：按用户名查库，判断是否已注册（查重）
    if existing_user:                                    # 查到了 → 用户名重复（用户名已存在）
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")  # 抛 400 异常：客户端请求有问题
    user = await users.create_user(db, user_data)        # 第二步：创建用户（密码会在 crud 里加密后入库）
    token = await users.create_token(db, user.id)        # 第三步：生成 Token（注册后直接登录，体验感好）
    # 期望返回的结构：
    # return {
    #   "code": 200,
    #   "message": "注册成功",
    #   "data": {
    #     "token": token,           # 注册立马可以登录，体验感好
    #     "userInfo": {
    #       "id": user.id,
    #       "username": user.username,
    #       "bio": user.bio,
    #       "avatar": user.avatar
    #     }
    #   }
    # }

    # 嵌套的响应结构：现有 code message data 结构，data 里面是一个对象，
    # 里面有 token 和 userInfo，userInfo 里面是一个对象，里面有 id username bio avatar

    # 第四步：用 Pydantic 模型统一格式化响应（组装响应数据）
    # UserInfoResponse.model_validate(user)：从 ORM 对象 user 中取属性 → 转成响应模型（需要模型类那配置 from_attributes=True）
    # UserAuthResponse：最外层 data 结构（token + userInfo）
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功", data=response_data)  # 统一响应


# ============================================================
# 接口2：用户登录  POST /api/user/login
# 流程：验证用户名密码 → 生成 Token → 返回
# ============================================================
@router.post("/login")
async def login(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    # 登录逻辑：验证用户是否存在 -> 验证密码 -> 生成 Token  → 响应结果
    user = await users.authenticate_user(db, user_data.username, user_data.password)  # 第一步：验证用户名+密码（内部会查库 + 比对密文）
    if not user:                                        # 验证失败（用户不存在 或 密码错误）
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")  # 抛 401 异常：未认证（不区分是用户不存在还是密码错，防泄露）
    token = await users.create_token(db, user.id)       # 第二步：验证通过 → 生成新 Token
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))  # 第三步：组装响应
    return success_response(message="登录成功啦", data=response_data)  # 统一响应


# 查Token查用户 → 封装crud → 功能整合成一个工具函数 → 路由导入使用: 依赖注入
# 依赖注入 get_current_user：从请求头 Authorization 取 Token → 查库验证 → 返回当前用户；无效/过期自动抛 401
# ============================================================
# 接口3：获取当前用户信息  GET /api/user/info
# ============================================================
@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):  # 直接注入当前用户，无需自己写验证逻辑
    return success_response(message="获取用户信息成功", data=UserInfoResponse.model_validate(user))  # 返回当前用户信息


# 修改用户信息：验证Token → 更新（用户输入数据 put 提交 → 请求体参数 → 定义Pydantic模型类） → 响应结果
# 参数：用户输入的 + 验证Token的 + db（调用更新的方法）
# ============================================================
# 接口4：修改用户信息  PUT /api/user/update
# ============================================================
@router.put("/update")
async def update_user_info(user_data: UserUpdateRequest, user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):  # 三个参数：请求体 + 当前用户(依赖注入) + 数据库会话(依赖注入)
    user = await users.update_user(db, user.username, user_data)  # 调用 crud 更新：只更新前端传了的字段，返回最新用户
    return success_response(message="更新用户信息成功", data=UserInfoResponse.model_validate(user))  # 返回更新后的用户信息


# ============================================================
# 接口5：修改密码  PUT /api/user/password
# 请求体：{"oldPassword": "xx", "newPassword": "xx"}
# ============================================================
@router.put("/password")
async def update_password(
        password_data: UserChangePasswordRequest,       # 请求体：oldPassword + newPassword（旧密码+新密码，Pydantic 校验）
        user: User = Depends(get_current_user),         # 依赖注入：当前登录用户
        db: AsyncSession = Depends(get_db)):            # 依赖注入：数据库会话（数据库操作：密码更新）
    # 调用 crud：校验旧密码 → 新密码加密 → 更新；返回 True/False
    res_change_pwd = await users.change_password(db, user, password_data.old_password, password_data.new_password)
    if not res_change_pwd:                              # 旧密码验证失败 → 修改失败
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="修改密码失败，请稍后再试")  # 抛 500 异常
    return success_response(message="修改密码成功")       # 修改成功 → 返回成功提示（无需返回数据）
