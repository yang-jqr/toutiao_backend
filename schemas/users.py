# ============================================================
# schemas 层：users.py —— 用户模块请求/响应模型
# 职责：参数校验 + 响应数据格式化（驼峰命名给前端）
# ============================================================

from typing import Optional  # 可选类型

from pydantic import BaseModel, Field, ConfigDict  # Pydantic：模型基类 / 字段定义 / 模型配置


# 注册/登录的请求体模型：{"username": "xx", "password": "xx"}
class UserRequest(BaseModel):
    username: str   # 用户名（必填）
    password: str   # 密码（必填）


# user_info 对应的类：基础类 + Info 类（id、用户名）
class UserInfoBase(BaseModel):
    """
    用户信息基础数据模型
    """
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")     # 昵称（可选，最长50）
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")    # 头像（可选）
    gender: Optional[str] = Field(None, max_length=10, description="性别")       # 性别（可选）
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")     # 简介（可选）


class UserInfoResponse(UserInfoBase):  # 继承基础信息 + 加 id/username
    id: int       # 用户ID
    username: str # 用户名

    # 模型类配置
    model_config = ConfigDict(
        from_attributes=True  # 允许从 ORM 对象属性中取值
    )


# data 数据类型：登录/注册返回的 token + userInfo
class UserAuthResponse(BaseModel):
    token: str                                       # 登录凭证 Token
    user_info: UserInfoResponse = Field(..., alias="userInfo")  # 用户信息（前端字段名 userInfo）

    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True,  # alias / 字段名兼容
        from_attributes=True  # 允许从 ORM 对象属性中取值
    )


# 更新用户信息的模型类（PUT 提交，只更新前端传的字段）
class UserUpdateRequest(BaseModel):
    nickname: str = None  # 昵称（默认 None = 不更新）
    avatar: str = None    # 头像
    gender: str = None    # 性别
    bio: str = None       # 简介
    phone: str = None     # 手机号


# 修改密码的请求体模型：{"oldPassword": "xx", "newPassword": "xx"}
class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(..., alias="oldPassword", description="旧密码")  # 旧密码（必填）
    new_password: str = Field(..., min_length=6, alias="newPassword", description="新密码")  # 新密码（必填，至少6位）
