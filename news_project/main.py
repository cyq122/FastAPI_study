from fastapi import FastAPI
from backend.routers import news,user
from fastapi.middleware.cors import CORSMiddleware
from backend.utils.exception_handlers import register_exception_handlers


app = FastAPI()

register_exception_handlers(app)
app.include_router(news.router)
app.include_router(user.router)

origins = [
    "http://localhost",
    "http://localhost:3000",
]
# 解决跨域报错（浏览器向另一个源的服务器发起了跨域HTTP请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # 设置允许的源
    allow_credentials=True, # 设置允许的cookie
    allow_methods=["*"],    # 设置允许的请求方法
    allow_headers=["*"],    # 设置允许的请求头
)