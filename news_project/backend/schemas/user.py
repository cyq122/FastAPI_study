from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class UserRequest(BaseModel):
    username:str
    password:str

#user_info数据类型 ：基础类+Info类（id、用户名）
class UserInfoBase(BaseModel):
    nickname:Optional[str] = Field(None,max_length=50,description="昵称")
    avatar:Optional[str] = Field(None,max_length=255,description="头像URL")
    gender:Optional[str] = Field(None,max_length=10,description="性别")
    bio:Optional[str] = Field(None,max_length=500,description="简介")

    
class UserInfoResponse(UserInfoBase):
    id:int
    username:str
    #模型类配置
    model_config = ConfigDict(from_attributes=True)# 允许从ORM对象属性中取值

#data数据类型
class UserAuthResponse(BaseModel):
    token:str
    user_info:UserInfoResponse = Field(...,alias="userInfo")

    #模型类配置
    model_config = ConfigDict(populate_by_name=True# alias / 字段名兼容
                              ,from_attributes=True# 允许从ORM对象属性中取值
                            )
#更新用户信息
class UserUpdateRequest(BaseModel):
    nickname:str = None
    avatar:str = None
    gender:str = None
    bio:str = None
    phone:str = None

#修改用户密码
class UserUpdatePasswordRequest(BaseModel):
    old_password:str=Field(...,description="旧密码",alias="oldPassword")
    new_password:str=Field(...,min_length=6,description="新密码",alias="newPassword")
