# ============================================================
# Redis 缓存配置：config/cache_conf.py
# 职责：创建 Redis 连接 + 封装缓存的读取/写入方法 封装方法 复用 工程化逻辑
# 缓存的作用：把高频查询的数据放内存(Redis)里，减少数据库压力，加快响应
# ============================================================

import json  # JSON 序列化/反序列化（存列表/字典用）
import os  # os：读取环境变量（Redis 地址/端口来自 .env）
from typing import Any  # 任意类型

from dotenv import load_dotenv  # load_dotenv：把 .env 文件里的配置加载成环境变量

import redis.asyncio as redis  # Redis 异步客户端

# ============================================================
# Redis 连接配置（集中管理，避免魔法数字）
# 为什么不直接写死在 redis.Redis(...) 调用里？
#   1. 配置集中在一处，好改：将来 Redis 换地址/端口，只改这里，
#      不用在业务代码里翻找。
#   2. 有名字可读性高：REDIS_PORT = 6379 一看就知道是端口；
#      直接写 6379 就是"魔法数字"，别人读代码要猜含义。
#   3. 现在已经抽到 .env 了：上面这三项都改成从环境变量注入
#      （REDIS_HOST = os.getenv("REDIS_HOST", "localhost")），
#      换环境只改 .env，代码零改动。
# 配置从 .env 读取（见项目根目录 .env.example）
# ============================================================
load_dotenv()  # 读取 .env，把配置注入 os.environ

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")  # Redis 服务器地址
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))  # Redis 默认端口
REDIS_DB = int(os.getenv("REDIS_DB", "0"))         # 数据库编号（0~15）


# 创建 Redis 的连接对象（引用上面的配置变量，保证只维护一处配置）
redis_client = redis.Redis(
    host=REDIS_HOST,  # Redis 服务器的主机地址 ← 引用 REDIS_HOST
    port=REDIS_PORT,  # Redis 端口号         ← 引用 REDIS_PORT
    db=REDIS_DB,  # Redis 数据库编号，0~15     ← 引用 REDIS_DB
    decode_responses=True  # 是否将字节数据解码为字符串
)


# 设置 和 读取（字符串 和 列表或字典）"[{}]"  一个设置缓存 ,两个读取
# 读取：字符串（原始字符串）
# Redis 连接失败、网络中断、服务未启动等情况，无法提前简单判断，所以使用 try...except：
# try：尝试执行可能出错的代码
# except：出错时执行，避免程序直接崩溃
async def get_cache(key: str):
    # return await redis_client.get(key)
    try:
        return await redis_client.get(key)  # 按 key 读取
    except Exception as e:  # 缓存失败不影响业务，打印日志并返回 None
        print(f"获取缓存失败：{e}")
        return None


# 读取：列表或字典（自动反序列化为 Python 对象）
async def get_json_cache(key: str):
    try:
        data = await redis_client.get(key)  # 读到的原始数据（JSON 字符串）
        if data:
            return json.loads(data)  # 反序列化：JSON 字符串 → 列表/字典
        return None
    except Exception as e:
        print(f"获取 JSON 缓存失败：{e}")
        return None


# ============================================================
# 设置缓存：set_cache(key, value, expire)
# 函数作用：把数据写入 Redis，并设置过期时间
# 参数说明：
#   key    -> 缓存的键（唯一标识，如 "news:1"）
#   value  -> 要存的值，任意类型（字符串/数字/列表/字典都行）
#   expire -> 过期时间，默认 3600 秒 = 1 小时（可选，不传就用默认值）
# setex 命令 = set(设置) + ex(expire 过期)，
#   一步完成"存值 + 设过期时间"，时间单位是秒
# ============================================================
async def set_cache(key: str, value: Any, expire: int = 3600):
    try:
        # isinstance() 判断传入的 value 是不是字典或列表
        if isinstance(value, (dict, list)):
            # 如果是，用 json.dumps() 把列表/字典转成 JSON 字符串
            # 因为 Redis 只能存字符串或字节，不能直接存 Python 对象
            # ensure_ascii=False：默认会把中文转成 \uXXXX 转义码，
            #   加 False 后中文保持原样，可读性好、也省空间
            value = json.dumps(value, ensure_ascii=False)  # 中文正常保存
        # 把处理好的值写入 Redis，同时设置过期时间(秒)
        await redis_client.setex(key, expire, value)  # setex：设置值 + 过期时间(秒)
        return True  # 成功返回 True，方便调用方知道"存成功了"
    except Exception as e:
        # 出错时打印日志方便排查，返回 False 告诉调用方"存失败了"
        # 核心思想：缓存失败不影响业务——Redis 挂了也只是没有缓存，请求照常走数据库
        print(f"设置缓存失败：{e}")
        return False
