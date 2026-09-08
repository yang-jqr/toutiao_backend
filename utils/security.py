# ============================================================
# utils 层：security.py —— 密码安全工具
# 职责：密码加密 + 密码验证（用 bcrypt 算法，密码不以明文存库）
# ============================================================

from passlib.context import CryptContext  # 密码哈希库

# 创建密码上下文：指定使用 bcrypt 加密算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 密码加密：把明文密码变成不可逆的密文
def get_hash_password(password: str):
    return pwd_context.hash(password)


# 密码验证: verify 返回值是布尔型（True=密码正确）
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
