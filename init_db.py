# ============================================================
# init_db.py —— 首次运行初始化
# 职责：确保数据库存在 → 建表 → 空库则填充种子数据
# 由 main.py 启动时自动调用，无需手动执行 SQL。
# ============================================================
import os
from datetime import datetime

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine

from config.db_conf import SERVER_DATABASE_URL, AsyncSessionLocal, DB_NAME
from models.base import Base
from models.news import Category, News


# 种子数据
SEED_CATEGORIES = [
    ("头条", 1), ("社会", 2), ("国内", 3), ("国际", 4),
    ("娱乐", 5), ("体育", 6), ("科技", 7), ("财经", 8),
]

SEED_NEWS = [
    ("国家主席发表2024年新年贺词", "回顾成就，展望未来，强调高质量发展。",
     "2023年12月31日晚，国家主席通过中央广播电视总台和互联网发表新年贺词。他回顾了过去一年在经济建设、科技创新等方面取得的成就，并强调要坚持稳中求进，推动高质量发展，增进民生福祉。",
     "https://picsum.photos/id/100/200/200", "新华社", 1, 12500, datetime(2024, 1, 1, 8, 0, 0)),
    ("2023年我国GDP同比增长5.2%", "经济总量超126万亿元，国民经济回升向好。",
     "国家统计局公布数据显示，2023年我国国内生产总值达到1260582亿元，按不变价格计算同比增长5.2%。全年社会消费品零售总额实现增长，就业形势总体稳定。",
     "https://picsum.photos/id/103/200/200", "经济日报", 1, 15300, datetime(2024, 1, 17, 10, 0, 0)),
    ("我国成功发射通信技术试验卫星十一号", "卫星顺利进入预定轨道。",
     "2024年1月10日，我国在西昌卫星发射中心使用长征二号丁运载火箭，成功将通信技术试验卫星十一号发射升空，将用于开展多频段、高速率通信试验。",
     "https://picsum.photos/id/102/200/200", "央视新闻", 1, 11200, datetime(2024, 1, 10, 18, 20, 0)),
    ("社区开展老年人数字技能培训", "帮助老人跨越数字鸿沟。",
     "某社区服务中心开展为期一周的老年人智能手机培训，志愿者手把手教学微信视频、网上挂号、防诈骗知识。活动有效帮助老人融入数字生活。",
     "https://picsum.photos/id/152/200/200", "社区报", 2, 4500, datetime(2025, 9, 21, 14, 20, 0)),
    ("爱心企业向福利院捐赠物资", "价值20万元的冬季保暖用品送达老人手中。",
     "多家企业联合向市福利院捐赠羽绒服、电热毯等过冬物资，志愿者们还表演节目陪伴老人，让孤寡老人感受到社会温暖。",
     "https://picsum.photos/id/156/200/200", "公益时报", 2, 3900, datetime(2025, 9, 17, 15, 30, 0)),
    ("农民合作社助力乡村振兴", "特色农产品网上销售，农户年收入增三成。",
     "某村成立专业合作社，整合当地特色农产品通过电商平台销售，去年帮助农户平均增收30%，让年轻人实现在家门口创业。",
     "https://picsum.photos/id/159/200/200", "农村新报", 2, 4800, datetime(2025, 9, 14, 10, 40, 0)),
]


async def init_db():
    """确保库存在 → 建表 → 空库则填充种子数据"""
    # 1) 确保数据库存在（用不带库名的连接串建库）
    server_engine = create_async_engine(SERVER_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        async with server_engine.connect() as conn:
            await conn.execute(
                text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                     f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    finally:
        await server_engine.dispose()

    # 2) 建表（所有模型共享同一个 Base，一次建出全部表）
    from config.db_conf import async_engine
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3) 空库则填充种子数据
    async with AsyncSessionLocal() as session:
        cat_count = (await session.execute(select(func.count(Category.id)))).scalar_one()
        if cat_count == 0:
            for name, order in SEED_CATEGORIES:
                session.add(Category(name=name, sort_order=order))
            await session.commit()

        news_count = (await session.execute(select(func.count(News.id)))).scalar_one()
        if news_count == 0:
            for title, desc, content, image, author, cid, views, pub in SEED_NEWS:
                session.add(News(title=title, description=desc, content=content, image=image,
                                 author=author, category_id=cid, views=views, publish_time=pub))
            await session.commit()
