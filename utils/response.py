# ============================================================
# utils 层：response.py —— 统一响应工具
# 职责：把成功响应统一格式化为 {code, message, data} 返回
# ============================================================

from fastapi.responses import JSONResponse     # JSON 响应对象
from fastapi.encoders import jsonable_encoder  # 序列化工具：把对象转成可 JSON 化的数据


def success_response(message: str = "success", data=None):
    """统一成功响应：返回 {code: 200, message, data}"""
    content = {
        "code": 200,        # 业务状态码：成功
        "message": message, # 提示信息
        "data": data        # 实际数据（将来传入的类型可能很复杂，比如 Pydantic/ORM 对象）
    }

    # 目标：把任何的 FastAPI、Pydantic、ORM 对象 都要正常响应 → code、message、data
    # jsonable_encoder 会把 ORM/Pydantic 对象/日期等转成普通 JSON 数据
    # 因为 data 的类型不知道，如果直接 return 会报错，必须能够解析 data 对象
    return JSONResponse(content=jsonable_encoder(content))
