from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.post('/api/test-success')
async def test_post(
    request:Request
):
    form = await request.form()

    return (
        {
            'result':form
        }
    )