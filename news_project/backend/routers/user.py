from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from backend.config.db_conf import get_db
from backend.schemas.user import UserAuthResponse, UserInfoResponse, UserRequest, UserUpdateRequest,UserUpdatePasswordRequest
from backend.crud import user
from backend.crud.user import authenticate_user, create_token, create_user, get_user_by_token, get_user_by_username, update_user,change_password
from backend.utils.response import success_response
from backend.utils.auth import get_current_user
from backend.models.user import User


router = APIRouter(prefix="/api/user",tags=["user"])

# 注册
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
    return success_response(message="注册成功",data=response_data)

# 登录
@router.post("/login")
async def login(user_data:UserRequest, db:AsyncSession = Depends(get_db)):
    #登录逻辑：验证用户是否存在 ——> 验证密码是否正确 ——> 生成Token ——> 响应结果
    existing = await user.authenticate_user(db,user_data.username,user_data.password)
    if not existing:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="用户或密码错误")
    user_token = await user.create_token(db,existing.id)
    response_data = UserAuthResponse(token=user_token,user_info=UserInfoResponse.model_validate(existing))
    return success_response(message="登录成功",data=response_data)

# 获取用户信息
@router.get("/info")
async def get_user_info(user:User= Depends(get_current_user),db:AsyncSession = Depends(get_db)):
    # 通过token查用户信息 ——> （封装方法）——> 路由导入使用 

    return success_response(message="获取用户信息成功",data=UserInfoResponse.model_validate(user))


# 修改用户信息：验证token ——> 修改用户信息（put提交、请求体参数、定义Pydantic模型类） ——> 响应结果
#参数：用户输入 + token验证 + db（调用更新方法）
@router.put("/update")
async def update_user_info(user_data:UserUpdateRequest,user:User= Depends(get_current_user),db:AsyncSession = Depends(get_db)):
    user = await update_user(db,user.username,user_data)
    return success_response(message="修改用户信息成功",data=UserInfoResponse.model_validate(user))

#修改密码
@router.put("/password")
async def update_password(password_date:UserUpdatePasswordRequest,user:User= Depends(get_current_user),db:AsyncSession = Depends(get_db)):
    changed_pwd = await change_password(db,user,password_date.old_password,password_date.new_password)
    if not changed_pwd:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="修改密码失败")
    return success_response(message="修改密码成功")