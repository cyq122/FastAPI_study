from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import DateTime, Float, String, delete, func, select
from pydantic import BaseModel, Field

app=FastAPI()

#1.创建异步引擎
ASYNC_DATABASE_URL="mysql+aiomysql://root:12345678@localhost:3306/fastapi_test?charset=utf8"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo  = True,       #log
    pool_size = 10,     #设置连接池活跃的连接数
    max_overflow = 20   #允许额外的连接数
)

#2.定义模型类
#2.1基类，继承DeclarativeBase（包含通用属性和字段的映射）：创建时间、更新时间，书籍表：id、书名、作者、价格、出版社
#2.2定义数据库表对应的模型类

class Base(DeclarativeBase):
    create_time:Mapped[datetime] = mapped_column(DateTime,insert_default=func.now(),default=func.now(),comment="创建时间")
    update_time:Mapped[datetime] = mapped_column(DateTime,insert_default=func.now(),default=func.now(),onupdate=func.now(),comment="修改时间")

class Book(Base):
    __tablename__ = "book"
    id:Mapped[int] = mapped_column(primary_key=True,comment="书籍id")
    bookname:Mapped[str] = mapped_column(String(255),comment="书名")
    author:Mapped[str] = mapped_column(String(255),comment="作者")
    price:Mapped[float] = mapped_column(Float,comment="书的价格")
    public:Mapped[str] = mapped_column(String(255),comment="出版社")

#3.创建数据库表
#3.1从连接池获取异步连接，开启事务，执行ORM操作
#3.2FastAPI应用启动时，创建数据库表

async def create_tables():
    #获取数据库异步引擎，创建事务 - 建表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) #Base 模型类的元数据创建

@app.on_event("startup")
async def startup_event():
    await create_tables()


#需求：查询功能的接口，查询图书 ——> 依赖注入：创建依赖项获取数据库会话 + Depends注入路由处理函数

#创建会话工厂
AsyncSessionLocal =async_sessionmaker(
    bind = async_engine,#绑定数据库引擎
    class_=AsyncSession,#指定会话类
    expire_on_commit=False #提交会话后不过期，不会重新查询数据库
)

#创建依赖项
async def get_database():
    async with AsyncSessionLocal() as session:#和数据库建立会话
        try:
            yield session   #把session会话给路由处理函数
            await session.commit()  #提交数据库改动
        except Exception:
            await session.rollback()    #有异常，回滚
            raise
        #async with...本身会自动执行close()操作
        # finally:
        #     await session.close()       #关闭会话

#注入依赖项
@app.get("/book/book{id}")
async def get_book_list(id :int,db:AsyncSession = Depends(get_database)):
    #查询操作为例
    result_all = await db.execute(select(Book))
    #book_all  = result_all.scalars().all()
    #book_one = result_all.scalars().first()
    book_one1 = await db.get(Book,2)
#条件查询
    book_one2 = await db.scalar(select(Book).where(Book.id==id))
    return book_one2

#查询价格>=100
@app.get("/books/bookprice")
async def get_book_list(db:AsyncSession = Depends(get_database)):
    #查询操作为例
    books = await db.scalars(select(Book).where(Book.price>=100))
    return books.all()

#模糊查询like("") %：0、1或多个字符   _：一个单个字符
#查找图书作者以c开头
@app.get("/books/bookauthor")
async def get_book_author(db:AsyncSession = Depends(get_database)):
    #查询操作为例
    #books = await db.scalars(select(Book).where(Book.author.like("c%") & (Book.price>=100)))
    #books = await db.scalars(select(Book).where(Book.author.like("c%") & (Book.price>=100)))
    #需求：数据库里的书籍id如果在书籍id列表里就返回
    id_list = [1,3,5]
    books = await db.scalars(select(Book).where(Book.id.in_(id_list)))
    return books.all()

#聚合查询
@app.get("/books/booksearch")
async def get_book_author(db:AsyncSession = Depends(get_database)):
    books_count = await db.scalar(select(func.count(Book.id)))
    books_avgprice = await db.scalar(select(func.avg(Book.price)))
    max_price = await db.scalar(select(func.max(Book.price)))
    min_price = await db.scalar(select(func.min(Book.price)))
    return {"books_count":books_count,"books_avgprice":books_avgprice,"max_price":max_price,"min_price":min_price}


#分页查询
@app.get("/books/bookpageS")
async def get_book_page(
    page: int = 1,
    page_size: int = 3,
    db:AsyncSession = Depends(get_database)
):
    #offset:跳过的记录数 limit：每页显示的记录数
    result = await db.scalars(select(Book).offset((page - 1) * page_size).limit(page_size))
    return result.all()

#增加add
#需求：用户输入图书信息（id、书名、作者、价格、出版社）
#用户输入：参数，使用请求体
class BookBase(BaseModel):
    #id:int 主键，自增
    bookname:str
    author:str
    price:float
    public:str

@app.post("/books/add")
async def add_book(book:BookBase, db:AsyncSession = Depends(get_database)):
    #定义ORM对象
    book_obj = Book(**book.__dict__)
    #add
    db.add(book_obj)
    #commit
    await db.commit()
    return book

#更新updata
#需求：修改图书信息，先查再改
#设计思路：路径参数：书籍id，查找，请求体：更新数据（书名、作者、价格、出版商）
class Bookupdata(BaseModel):
    bookname:str
    author:str
    price:float
    public:str

@app.put("/books/updata/{id}")
async def updata_book(id: int, data: Bookupdata, db: AsyncSession = Depends(get_database)):
    #先查询
    book_data = await db.get(Book,id)
    if book_data is None:
        raise HTTPException(status_code=404,detail="查无此书")
    #更新，重新赋值
    book_data.bookname = data.bookname
    book_data.author = data.author
    book_data.price = data.price
    book_data.public = data.public
    #提交更新
    await db.commit()
    return book_data 

#删除delete
#设计思路：路径参数：书籍id，查找，请求体：根据id删除
@app.delete("/book/delete/{id}")
async def delete_book(id: int, db: AsyncSession = Depends(get_database)):
    #查询
    book_data = await db.get(Book,id)
    if book_data is None:
        raise HTTPException(status_code=404,detail="查无此书")
    #删除
    await db.delete(book_data)
    await db.commit()
    return {f"id:{id}的书已删除！"}