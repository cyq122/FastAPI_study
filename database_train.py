from datetime import datetime
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import DateTime, Float, String, func,Integer, select

app = FastAPI()

#创建异步引擎
ASYNC_DATABASE_URL="mysql+aiomysql://root:12345678@localhost:3306/fastapi_test?charset=utf8"

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo = True,
    pool_size = 10,
    max_overflow = 20
)

#定义模型类
#定义基类
class Base(DeclarativeBase):
    create_time:Mapped[datetime] = mapped_column(DateTime,insert_default=func.now(),default=func.now(),comment="创建时间")
    update_time:Mapped[datetime] = mapped_column(DateTime,insert_default=func.now(),default=func.now(),onupdate=func.now(),comment="更新时间")

#定义数据库表-用户表：id、用户名、密码、创建时间、更新时间
class User(Base):
    __tablename__ = "user"

    id:Mapped[int] = mapped_column(primary_key=True,comment="用户id")
    name:Mapped[str] = mapped_column(String(255),comment="用户名")
    password:Mapped[str] = mapped_column(String(255),comment="密码")

#创建数据库表
#定义创建数据表函数
async def create_table():
    #获取数据库异步引擎
    async with  async_engine.begin() as conn:
        #模型元数据创建
        await conn.run_sync(Base.metadata.create_all)

#启动FastAPI时，开始创建数据表

@app.on_event("startup")
async def startup_event():
    await create_table()

#依赖注入 - 查询功能接口

#创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind = async_engine,
    class_= AsyncSession,
    expire_on_commit=False
)
#创建依赖项
async def get_databse():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

#注入依赖
@app.get("/users/user")
async def get_user_list(db:AsyncSession = Depends(get_databse)):
    #查询操作
    result = await db.execute(select(User))
    user = result.scalars().all()
    return user