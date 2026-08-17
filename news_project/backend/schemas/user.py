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