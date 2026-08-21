from datetime import datetime, timedelta
import uuid

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import User,UserToken
from backend.schemas.user import UserRequest,UserUpdateRequest
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

async def authenticate_user(db:AsyncSession,username:str,password:str):
    user = await get_user_by_username(db,username)
    if not user or not security.verify_password(password,user.password):
        return None

    return user


#根据token查询用户
async def get_user_by_token(db:AsyncSession,token:str):
    result0 = await db.execute(select(UserToken).where(UserToken.token==token))
    db_token = result0.scalar_one_or_none()
    if not db_token or db_token.expires_at < datetime.now():
        return None

    result1 = await db.execute(select(User).where(User.id==db_token.user_id))
    user = result1.scalar_one_or_none()
    return user


#更新用户信息
async def update_user(db:AsyncSession,user_name:str,user_data:UserUpdateRequest):
    #没有设置值的不更新
    result = await db.execute(update(User).where(User.username==user_name).values(**user_data.model_dump(exclude_unset=True,exclude_none=True)))
    await db.commit()
    #检查更新
    if result.rowcount == 0:
        raise HTTPException(status_code=404,detail="用户不存在")
    #获取更新后的用户
    new_user = await get_user_by_username(db,user_name)
    return new_user

#更新密码
async def change_password(db:AsyncSession,user:User,old_pwd:str,new_pwd:str):
    if not security.verify_password(old_pwd,user.password):
        return False
    user.password = security.get_hash_password(new_pwd)
    db.add(user)    #更新：由SQLAlchemy 真正接管User对象，确保commit，规避session过期或关闭导致的不能提交的问题
    await db.commit()
    await db.refresh(user)
    return True