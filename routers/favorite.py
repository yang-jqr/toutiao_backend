# ============================================================
# 路由层：favorite.py —— 收藏模块接口
# 职责：接收请求 → 调用 crud 层处理 → 返回统一响应
# 所有接口都需要登录（依赖 get_current_user 验证 Token）
# ============================================================

# 导入需要用到的类
from fastapi import APIRouter, Query, Depends, HTTPException  # APIRouter路由 / Query查询参数校验 / Depends依赖注入 / HTTPException异常
from sqlalchemy.ext.asyncio import AsyncSession              # 异步会话类型（类型标注用）
from starlette import status                                 # HTTP 状态码常量

from config.db_conf import get_db                            # 数据库会话依赖
from models.users import User                                # 用户模型（标注当前登录用户类型）
from schemas.favorite import FavoriteCheckResponse, FavoriteAddRequest, FavoriteListResponse  # 收藏相关请求/响应模型
from utils.auth import get_current_user                      # 依赖项：验证 Token 返回当前用户
from utils.response import success_response                  # 统一成功响应格式
from crud import favorite                                    # crud 层：收藏的数据库操作

# 创建路由实例：前缀 /api/favorite，文档分组 favorite
router = APIRouter(prefix="/api/favorite", tags=["favorite"])


# ============================================================
# 接口1：检查是否已收藏  GET /api/favorite/check?newsId=xx
# 参数：newsId 必填查询参数 + 当前登录用户 + 数据库会话
# ============================================================
@router.get("/check")
async def check_favorite(
        news_id: int = Query(..., alias="newsId"),  # 必填查询参数，前端传的是 newsId（... 表示必填）
        user: User = Depends(get_current_user),     # 依赖注入：Token 验证通过后的当前用户
        db: AsyncSession = Depends(get_db)          # 依赖注入：数据库会话
):
    # 调用 crud：查询收藏表，判断该用户是否收藏了这条新闻（返回布尔值）
    is_favorited = await favorite.is_news_favorite(db, user.id, news_id)  # 参数按顺序传递 → isFavorite → 整个构造出来 → 模型类
    # 用响应模型格式化（isFavorite 驼峰命名给前端）后返回
    return success_response(message="检查收藏状态成功", data=FavoriteCheckResponse(isFavorite=is_favorited))


# ============================================================
# 接口2：添加收藏  POST /api/favorite/add
# 请求体：{"newsId": 1}
# ============================================================
@router.post("/add")
async def add_favorite(
        data: FavoriteAddRequest,               # 请求体：Pydantic 校验（newsId）
        user: User = Depends(get_current_user), # 当前登录用户
        db: AsyncSession = Depends(get_db)      # 数据库会话
):
    # 调用 crud：往收藏表插入一条记录（user_id + news_id），返回收藏对象
    result = await favorite.add_news_favorite(db, user.id, data.news_id)
    return success_response(message="添加收藏成功", data=result)


# ============================================================
# 接口3：取消收藏  DELETE /api/favorite/remove?newsId=xx
# ------------------------------------------------------------
# 为什么这里用"查询参数"？
# - 删的是"当前用户 与 某条新闻 的收藏关系"，真正主语是登录用户（Token 决定），newsId 只是筛选条件
# - 查询参数 = 筛选条件/选项 → ?newsId=5 表示"把当前用户对新闻5的收藏删掉"
# - 对比历史删除接口用路径参数 /delete/{history_id}，因为那是定位一条独立的记录
# 记法：路径参数定位资源；查询参数当筛选条件/选项（可省略、可组合）
# ============================================================
@router.delete("/remove")
async def remove_favorite(
        news_id: int = Query(..., alias="newsId"),  # 必填查询参数 newsId
        user: User = Depends(get_current_user),     # 当前登录用户
        db: AsyncSession = Depends(get_db)          # 数据库会话
):
    # 调用 crud：删除收藏记录，返回是否删除成功（rowcount > 0）
    result = await favorite.remove_news_favorite(db, user.id, news_id)
    if not result:  # 没删到 → 记录不存在
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏记录不存在")
    return success_response(message="删除收藏成功")


# ============================================================
# 接口4：收藏列表  GET /api/favorite/list?page=1&pageSize=10
# 返回：list（新闻+收藏时间+收藏id）+ total + hasMore（分页）
# ============================================================
@router.get("/list")
async def get_favorite_list(
        page: int = Query(1, ge=1),                                # 页码，默认1，最小1
        page_size: int = Query(10, ge=1, le=100, alias="pageSize"), # 每页条数，默认10，最大100
        user: User = Depends(get_current_user),                     # 当前登录用户
        db: AsyncSession = Depends(get_db)                          # 数据库会话
):
    # 调用 crud 联表查询：返回 (rows, total)
    # rows 的每个元素是 (新闻对象, 收藏时间, 收藏id)
    rows, total = await favorite.get_favorite_list(db, user.id, page, page_size)
    # 把每行转成字典：新闻对象的所有字段 + 收藏时间 + 收藏id（** 解包字典）
    # 列表推导式
    favorite_list = [{
        **news.__dict__,            # 新闻对象的全部字段（id/title/image...）
        "favorite_time": favorite_time,  # 收藏时间
        "favorite_id": favorite_id       # 收藏记录id
    } for news, favorite_time, favorite_id in rows]
    # 当前已取到的条数（page*page_size）< 总量 → 还有下一页
    has_more = total > page * page_size

    # 组装分页响应（list/total/hasMore）定义响应的模型类
    data = FavoriteListResponse(list=favorite_list, total=total, hasMore=has_more)
    return success_response(message="获取收藏列表成功", data=data)


# ============================================================
# 接口5：清空收藏  DELETE /api/favorite/clear
# ============================================================
@router.delete("/clear")
async def clear_favorite(
        user: User = Depends(get_current_user),  # 当前登录用户
        db: AsyncSession = Depends(get_db)       # 数据库会话
):
    # 调用 crud：删除该用户所有收藏记录，返回删除条数
    count = await favorite.remove_all_favorites(db, user.id)
    return success_response(message=f"清空了{count}条记录")

