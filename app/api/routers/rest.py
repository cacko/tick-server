from pathlib import Path
from fastapi import APIRouter, Depends, Request
import logging
from app.api.auth import check_auth
from app.lametric import LaMetric
from app.lametric.models import CONTENT_TYPE
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.post("/status")
async def status(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    return LaMetric.queue.put_nowait((CONTENT_TYPE.LIVESCOREEVENT, payload))


@router.put("/nowplaying")
async def nowplaying(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    logging.info(payload)
    return LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, payload))


@router.post("/nowplaying")
async def post_nowplaying(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    logging.info(payload)
    return LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, payload))


@router.post("/subscription")
async def on_subscription(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    return LaMetric.queue.put_nowait((CONTENT_TYPE.LIVESCOREEVENT, payload))


@router.get("/privacy", response_class=HTMLResponse)
async def privacy():
    html_path = Path(__file__).parent / "views" / "privacy.tpl"
    return html_path.read_text()
