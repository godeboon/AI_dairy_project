from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter


router = APIRouter()


# 템플릿 경로 지정
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_main_page(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})



@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})




@router.get("/mypage_edit", response_class=HTMLResponse)
async def mypage_edit(request: Request):
    return templates.TemplateResponse("mypage_edit.html", {"request": request})

@router.get("/chatroom", response_class=HTMLResponse)
async def chatroom():
    return templates.TemplateResponse("chat.html", {"request": {}})

@router.get("/metaverse", response_class=HTMLResponse)
def metaverse_page(request: Request):
    return templates.TemplateResponse("metaverse.html", {"request": request})



@router.get("/templates/components/chatting/sub_chat_list.html", response_class=HTMLResponse)
async def space_section(request: Request):
    with open("templates/components/chatting/sub_chat_list.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
    



@router.get("/templates/components/space/section.html", response_class=HTMLResponse)
async def space_section(request: Request):
    with open("templates/components/space/section.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/templates/components/study/section.html", response_class=HTMLResponse)
async def study_section(request: Request):
    with open("templates/components/study/section.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/templates/components/chatting/section.html", response_class=HTMLResponse)
async def chatting_section(request: Request):
    with open("templates/components/chatting/section.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/templates/components/garden/section.html", response_class=HTMLResponse)
async def garden_section(request: Request):
    with open("templates/components/garden/section.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/templates/components/garden/sub_seed_made.html", response_class=HTMLResponse)
async def garden_sub_seed_made(request: Request):
    with open("templates/components/garden/sub_seed_made.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/templates/components/study/sub_diary_generate.html", response_class=HTMLResponse)
async def chatting_section(request: Request):
    with open("templates/components/study/sub_diary_generate.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/templates/components/study/encourage.html", response_class=HTMLResponse)
async def encourage_section(request: Request):
    with open("templates/components/study/encourage.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())    


print("✅ [html_router.py] 파일 로딩됨")
print("✅ router 변수 존재 여부:", 'router' in globals())
