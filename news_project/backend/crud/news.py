from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.news import Category,News_list

# 获取所有分类
async def get_categories(db:AsyncSession,skip:int=0,limit:int=100):
    result = await db.scalars(select(Category).offset(skip).limit(limit))
    return result.all()

async def get_news_list(db:AsyncSession,category_id:int,skip:int=0,limit:int=10):
    # 获取新闻列表
    result = await db.scalars(select(News_list).where(News_list.category_id==category_id).offset(skip).limit(limit))
    return result.all()

async def get_news_count(db:AsyncSession,category_id:int):#获取指定分类下的新闻数量
    result = await db.execute(select(func.count(News_list.id)).where(News_list.category_id==category_id))
    return result.scalar_one()

async def get_news_detail(db:AsyncSession,id:int):
    result = await db.execute(select(News_list).where(News_list.id==id))
    return result.scalar_one_or_none()

async def increase_news_views(db:AsyncSession,id:int):
    result = await db.execute(update(News_list).where(News_list.id==id).values(views=News_list.views+1))
    await db.commit()

    return result.rowcount>0

async def get_related_news(db:AsyncSession,id:int,category_id:int,limit:int=5):
    #order_by()排序  limit()限制数量
    result = await db.execute(select(News_list).where(News_list.category_id==category_id,News_list.id != id).order_by(News_list.views.desc(),News_list.publish_time.desc()).limit(limit))
    #return result.scalars().all()
    related_news = result.scalars().all()
    #列表推导式 推导出新闻的核心数据，然后再return
    return [{
        "id":news_detail.id,
        "title":news_detail.title,
        "content":news_detail.content,
        "image":news_detail.image,
        "author":news_detail.author,
        "publishTime":news_detail.publish_time,
        "categoryId":news_detail.category_id,
        "views":news_detail.views,
    } for news_detail in related_news]