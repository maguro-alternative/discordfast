from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from starlette.middleware.sessions import SessionMiddleware

from threading import Thread
import uvicorn
import os

from routers import (
    line_bot,
    index,
    register,
    callback,
    guild,
    guilds,
    line_post,
    line_post_sucess,
    logout
)

app = FastAPI(
    docs_url=None, 
    redoc_url=None, 
    openapi_url=None,
    title='FastAPIを利用したDiscordログイン',
    description='OAuth2を利用してユーザー情報を取得するトークンを発行します。',
    version='0.9 beta'
)

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")
jinja_env = templates.env  #Jinja2.Environment : filterやglobalの設定用

# templates/static以下のファイルを静的に扱えるようにする
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# session使用
app.add_middleware(SessionMiddleware, secret_key="some-random-string")

# 各パス
app.include_router(index.router)
app.include_router(line_bot.router)
app.include_router(register.router)
app.include_router(callback.router)
app.include_router(guild.router)
app.include_router(guilds.router)
app.include_router(line_post.router)
app.include_router(line_post_sucess.router)
app.include_router(logout.router)

# ローカル実行
def local_run():
    uvicorn.run(
        app,
        host='localhost',  
        port=int(os.getenv("PORT", default=5000)), 
        log_level="info"
    )

# 本番環境
def run():
    uvicorn.run(
        "main_server:app",
        host="0.0.0.0", 
        port=int(os.getenv("PORT", default=8080)), 
        log_level="info"
    )

# DiscordBotと並列で立ち上げる
def keep_alive():
    if os.environ.get("PORTS") != None:
        t = Thread(target=local_run)
    else:
        t = Thread(target=run)
    t.start()