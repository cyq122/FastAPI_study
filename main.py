from fastapi import FastAPI,Path,Query,HTTPException
from pydantic import BaseModel,Field
from fastapi.responses import HTMLResponse,FileResponse

# 实例化app对象，创建FastAPI实例
app = FastAPI(title="FastAPI学习项目", version="0.1.0")

#uvicorn main:app --reload来运行项目

#访问API交互式文档：+docs
@app.get("/")
async def root():
    return {"message": "Hello FastAPI666"}

#访问/hello 响应结果 msg：你好 FastAPI
@app.get("/user/hello")
async def get_user_hello():
    return {"msg":"我正在学习FastAPI..."}

#练习
@app.get("/hello")
async def get_hello():
    return {"msg":"你好 FastAPI"}

#路径参数----------------------------------------------------------------------------------------

@app.get("/book/{id}")
async def get_book1(id: int):
    return {"id":id,"title":f"这是第{id}本书"}

#练习
@app.get("/user/{id}")
async def get_user(id: int):
    return {"id":id,"title":f"user{id}"}

@app.get("/book/{id}")
async def get_book2(id: int = Path(...,gt=0,le=100,description="书籍id，取值范围（1，100）")):
    return {"id":id,"title":f"这是第{id}本书"}

#练习1：查找书籍的作者，路径参数name，长度范围2-10
@app.get("/book_author/{name}")
async def get_book_author(name: str = Path(...,max_length=10,min_length=2,description="书籍的作者名字，取值范围（2，10）")):
    return {"title":f"这本书的作者是：{name}"}

#练习2 定义2个接口，携带路径参数，并使用Path来实现类型注解，接口1:以新闻分类id为参数，id范围1-100，接口2:以新闻名为参数，范围2-10
@app.get("/news/{id}/{name}")
async def get_news(id: int = Path(...,gt=1,le=100),name: str = Path(...,max_length=10,min_length=2)):
    return {"msg":f"这份新闻是第{id}类新闻，分类名称是：{name}"}

#查询参数----------------------------------------------------------------------------------------
#查询新闻 ->分页，skip：跳过的记录数，limit：返回的记录数
@app.get("/news/news_list")
async def get_news_list(
    skip: int = Query(0,description="跳过的记录数",lt=100),
    limit:int = Query(10,description="返回的记录数")
):
    return {"skip":skip,"limit":limit}

#练习
@app.get("/books/books_list")
async def get_books_list(
    classes: str = Query("Python开发",description="图书的分类",min_length=5,max_length=255),
    price:int = Query(...,description="图书的价格",gt=50,le=100)
):
    return {"图书的类别":{classes},"图书的价格":{price}}

#请求体----------------------------------------------------------------------------------------
#定义类型
class User(BaseModel):
    name:str=Field(default="cyq",min_length=2,max_length=10,description="用户名")
    password:str=Field(...,min_length=3,max_length=20)

#类型注解
@app.post("/register")
async def register(user:User):
    return user

#练习
class Book(BaseModel):
    bookname:str=Field(...,min_length=2,max_length=20)
    author:str=Field(...,min_length=2,max_length=10)
    public:str=Field(default="Python")
    price:int=Field(...,gt=0)

#类型注解
@app.post("/Bookcity")
async def book_inf(book:Book):
    return book

#响应类型----------------------------------------------------------------------------------------

#接口：响应HTML代码
@app.get("/html",response_class=HTMLResponse)
async def get_html():
    return "<h1>Hello World!!!</h1>"

#接口：返回图片内容
@app.get("/file")
async def get_file():
    file_path = "87621EA7-B17D-4F59-8435-D782470A8F3C_1_105_c.jpeg"
    return FileResponse(file_path)

#新闻接口：响应自定义数据格式
class News(BaseModel):
    id:int
    title:str
    content:str

@app.get("/response_news/{id}",response_model=News)
async def get_news_response(id: int):
    return{
        "id":id,
        "title":f"这是第{id}本书",
        "content":f"这是一本Python教程"
}

#异常处理----------------------------------------------------------------------------------------
#需求：按id查询新闻（1-6）
@app.get("/news_exception/{id}")
async def get_exception_news(id :int):
    id_list=[1,2,3,4,5,6]
    if id not in id_list:
        raise HTTPException(status_code=404,detail="您查找的新闻不存在")
    else:
        return {f"这是第{id}本书"}