#模块化路由：把每个业务功能的接口拆分到独立文件里，再统一挂载到主应用中

#模块化目录结构 ——> 编写独立路由模块 ——> 在main.py中挂载路由

#例子：
#1.编写独立路由模块
# from fastapi import APIRouter

# #创建APIRouter实例
# router = APIRouter(prefix="/api/news",tags=["news"])  #prefix：前缀   tags：分组

# @router.get("/categories")
# async def get_categories():
#     return {"msg":"获取分类成功"}

#2.在main.py中挂载路由
# from fastapi import FastAPI

# app = FastAPI(title="FastAPI学习项目", version="0.1.0")
# app.include_router(news.router)


#接口实现流程：
#1.模块化路由 ——> API接口规范文档
#2.定义模型类 ——> 数据库表（数据库设计文档）
#3.在 crud 文件夹里创建文件，封装操作数据库的方法
#4.在路由处理函数里调用 crud 封装好的方法，响应结果
from fastapi import APIRouter,Depends, HTTPException, Query
from backend.crud import news
from backend.config.db_conf import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/news",tags=["news"])

@router.get("/categories")
async def get_categories(db: AsyncSession=Depends(get_db),skip:int=0,limit:int=100):
    #获得数据库新闻的分类数据 ——> 定义模型类 ——> 封装查询数据的方法
    categories = await news.get_categories(db,skip,limit)
    return {
        "code":200,
        "message":"获取新闻分类成功",
        "data":categories
    }

@router.get("/list")
async def get_news_list(
    db: AsyncSession=Depends(get_db),
    category_id:int=Query(...,alias="categoryId"),#alias：别名
    page:int=1,
    page_size:int=Query(default=10,le=100,alias="pageSize")
):
    #思路：处理分页规则（分页查询）——> 查询新闻列表 ——> 计算总量 ——> 计算是否hasmore
    offset = (page-1)*page_size
    #获得数据库新闻的分类数据 ——> 封装查询数据方法
    news_list = await news.get_news_list(db,category_id,offset,page_size)
    count = await news.get_news_count(db,category_id)
    hasmore = (offset + len(news_list) < count)
    return {
        "code":200,
        "message":"获取新闻列表成功",
        "data":{
            "list":news_list,
            "total":count,
            "hasMore":hasmore
        }
    }

@router.get("/detail")
async def get_news_detail(id:int = Query(...,alias="id"),db:AsyncSession = Depends(get_db)):
    news_detail = await news.get_news_detail(db,id)
    if not news_detail:
        raise HTTPException(status_code=404,detail="新闻不存在")
    
    views_res = await news.increase_news_views(db,id)
    if not views_res:
        raise HTTPException(status_code=404,detail="新闻不存在")

    related_news = await news.get_related_news(db,news_detail.id,news_detail.category_id)
    return {
        "code":200,
        "message":"success",
        "data":{
            "id":news_detail.id,
            "title":news_detail.title,
            "content":news_detail.content,
            "image":news_detail.image,
            "author":news_detail.author,
            "publishTime":news_detail.publish_time,
            "categoryId":news_detail.category_id,
            "views":news_detail.views,
            "relatedNews":related_news
        }
    }