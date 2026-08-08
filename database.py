from datetime import datetime
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import DateTime, Float, String, func, select

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
@app.get("/books/book")
async def get_book_list(db:AsyncSession = Depends(get_database)):
    #查询操作为例
    result = await db.execute(select(Book))
    book = result.scalars().all()
    return book