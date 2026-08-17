from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from backend.config.db_conf import get_db
from backend.schemas.user import UserAuthResponse, UserInfoResponse, UserRequest
from backend.crud import user
from backend.utils.response import success_response


router = APIRouter(prefix="/api/user",tags=["user"])

@router.post("/register")
async def register(user_data:UserRequest, db:AsyncSession = Depends(get_db),):
    # 验证用户是否存在 ——> 创建用户 ——> 生成Token ——> 响应结果
    existing = await user.get_user_by_username(db,user_data.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="用户已存在")
    new_user = await user.create_user(db,user_data)    
    user_token = await user.create_token(db,new_user.id)
    # return {
    #     "code":200,
    #     "message":"注册成功",
    #     "data":{
    #         "token":user_token,
    #         "userInfo":{
    #             "id":new_user.id,
    #             "username":new_user.username,
    #             "bio":new_user.bio,
    #             "avatar":new_user.avatar,
    #         }
    #     }
    # }

    response_data = UserAuthResponse(token=user_token,user_info=UserInfoResponse.model_validate(new_user))
    return success_response(message="success",data=response_data)



