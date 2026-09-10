# ============================================================
# utils 层：security.py —— 密码安全工具
# 职责：密码加密 + 密码验证（用 bcrypt 算法，密码不以明文存库）
#
# 为什么需要这个文件？
#   1. 数据库中绝不能存明文密码（一旦数据库泄露，所有用户密码直接暴露，
#      而且很多用户在不同网站用同一个密码，会造成连锁泄密）
#   2. 本文件提供两个核心能力：
#      - get_hash_password()  注册/改密时：明文 → 密文，存库
#      - verify_password()    登录时：把用户输入的明文和库里的密文比对
# ============================================================

from passlib.context import CryptContext  # passlib 密码哈希库，提供 hash / verify 等加密校验方法

# 创建密码上下文：指定使用 bcrypt 加密算法
# - schemes=["bcrypt"]：选用 bcrypt 算法（加盐的单向哈希，业界主流、安全性高）
# - deprecated="auto"  ：自动处理旧格式/弃用的哈希方案，方便以后升级算法而不影响老数据
# - 每次加密都会自动随机加盐（salt），所以同一个密码每次生成的密文都不一样，
#   防止彩虹表攻击、撞库攻击
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 密码加密：把明文密码变成不可逆的密文
# 参数 password: 用户注册/修改密码时输入的明文密码（str）
# 返回: bcrypt 哈希后的密文字符串（形如 $2b$12$...，可直接存入数据库）
# 注意: 这是单向加密，密文无法反推出明文；比对密码只能靠 verify_password()
def get_hash_password(password: str):
    return pwd_context.hash(password)


# 密码验证: 把用户输入的明文密码 和 数据库里存的密文 进行比对
# 参数 plain_password : 用户登录时输入的明文密码
# 参数 hashed_password: 数据库里查出来的密文（之前加密入库的）
# 返回: 布尔值（True=密码正确，False=密码错误）
# 原理: 库内部会用密文中自带的 salt 重新哈希明文，再和密文比对，无需明文可逆
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
