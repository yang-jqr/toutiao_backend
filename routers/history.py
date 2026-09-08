# ============================================================
# 路由层：history.py —— 浏览历史模块接口
# 职责：接收请求 → 调用 crud 层处理 → 返回统一响应
# 所有接口都需要登录（依赖 get_current_user 验证 Token）
# ============================================================

# 导入需要用到的类
from fastapi import APIRouter, Depends, Query, HTTPException  # APIRouter路由 / Depends依赖注入 / Query查询参数校验 / HTTPException异常
from sqlalchemy.ext.asyncio import AsyncSession              # 异步会话类型（类型标注用）
from starlette import status                                 # HTTP 状态码常量

from config.db_conf import get_db                            # 数据库会话依赖
from crud import history                                     # crud 层：历史的数据库操作
from models.users import User                                # 用户模型（标注当前登录用户类型）
from schemas.history import HistoryAddRequest, HistoryNewsItemResponse, HistoryListResponse  # 历史相关请求/响应模型
from utils.auth import get_current_user                      # 依赖项：验证 Token 返回当前用户
from utils.response import success_response                  # 统一成功响应格式

# 创建路由实例：前缀 /api/history，文档分组 history
router = APIRouter(prefix="/api/history", tags=["history"])


# ============================================================
# 接口1：添加历史记录  POST /api/history/add
# 请求体：{"newsId": 1}
# 逻辑：如果已看过该新闻 → 更新时间；没看过 → 新增一条
# ============================================================
@router.post("/add")
async def add_history(data: HistoryAddRequest,               # 请求体：Pydantic 校验（newsId）
                      user: User = Depends(get_current_user),  # 当前登录用户
                      db: AsyncSession = Depends(get_db)):     # 数据库会话
    """
    添加历史记录
    """
    # 调用 crud：去重逻辑（已存在则刷新浏览时间），返回历史记录对象
    result = await history.add_history(db, user.id, data.news_id)
    return success_response(message="添加成功", data=result)


# ============================================================
# 接口2：历史记录列表  GET /api/history/list?page=1&pageSize=10
# 返回：list（新闻+浏览时间+历史id）+ total + hasMore（分页）
# ============================================================
@router.get("/list")
async def get_history_list(page: int = Query(1, ge=1),                                # 页码，默认1，最小1
                           page_size: int = Query(10, ge=1, le=100, alias="pageSize"), # 每页条数，默认10，最大100
                           user: User = Depends(get_current_user),                     # 当前登录用户
                           db: AsyncSession = Depends(get_db)):                        # 数据库会话
    """
    获取历史记录列表
    """
    # 调用 crud 联表查询：返回 (rows, total)
    # rows 的每个元素是 (新闻对象, 浏览时间, 历史id)
    rows, total = await history.get_history_list(db, user.id, page, page_size)

    # 当前已取到的条数 < 总量 → 还有下一页
    has_more = total > page * page_size

    # 把每行转成响应模型：新闻字段 + 浏览时间 + 历史id（model_validate 校验转换）
    history_list = [HistoryNewsItemResponse.model_validate({
        **news.__dict__,          # 新闻对象的全部字段
        "view_time": view_time,   # 浏览时间
        "history_id": history_id  # 历史记录id
    }) for news, view_time, history_id in rows]

    # 组装分页响应
    data = HistoryListResponse(list=history_list, total=total, hasMore=has_more)

    return success_response(data=data)


# ============================================================
# 接口3：删除历史记录  DELETE /api/history/delete/{history_id}
# 路径参数：history_id（注意和收藏不同，这里用路径参数）
# ============================================================
@router.delete("/delete/{history_id}")
async def delete_history(history_id: int,                     # 路径参数：要删除的历史记录id
                         user: User = Depends(get_current_user),  # 当前登录用户
                         db: AsyncSession = Depends(get_db)):     # 数据库会话
    """
    删除历史记录
    """
    # 调用 crud：删除记录，返回是否成功（rowcount > 0）
    result = await history.delete_history(db, user.id, history_id)
    if not result:  # 没删到 → 记录不存在
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="历史记录不存在")
    return success_response(message="删除成功")


# ============================================================
# 接口4：清空历史记录  DELETE /api/history/clear
# ============================================================
@router.delete("/clear")
async def clear_history(user: User = Depends(get_current_user),  # 当前登录用户
                        db: AsyncSession = Depends(get_db)):     # 数据库会话
    """
    清空历史记录
    """
    # 调用 crud：删除该用户所有历史记录，返回删除条数
    result = await history.clear_history(db, user.id)
    return success_response(message="清空成功")