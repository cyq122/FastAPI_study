from datetime import datetime, timedelta
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import User,UserToken
from backend.schemas.user import UserRequest
from backend.utils import security
#根据用户名查询用户
async def get_user_by_username(db:AsyncSession,username:str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

#创建用户add
async def create_user(db:AsyncSession,user_data:UserRequest):
    #先加密密码，再写入数据库
    hashpwd = security.get_hash_password(user_data.password)
    user = User(username=user_data.username,password=hashpwd)
    db.add(user)
    await db.commit()
    await db.refresh(user)#刷新，从数据库中读会最新的user
    return user


#生成Token
async def create_token(db:AsyncSession ,id:int):
    #生成Token + 设置过期时间  ——> 查询数据库当前用户是否有Token，若有：更新，若无：添加
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    result =  await db.execute(select(UserToken).where(UserToken.user_id==id))
    user_token = result.scalar_one_or_none()
    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        new_token = UserToken(user_id=id,token=token,expires_at=expires_at)
        db.add(new_token)
        await db.commit()

    return token