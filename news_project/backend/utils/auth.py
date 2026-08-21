from fastapi import Depends, Header,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.config.db_conf import get_db
from backend.crud.user import get_user_by_token
from starlette import status

#根据token查询用户，最后返回用户
async def get_current_user(authorization:str = Header(...,alias="Authorization"),db:AsyncSession = Depends(get_db)):
    # token = authorization.split(" ")[1]
    user = await get_user_by_token(db,authorization)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="令牌过期或无效")
    return user