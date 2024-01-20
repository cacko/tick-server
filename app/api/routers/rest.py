from pathlib import Path
from fastapi import APIRouter, Depends, Request
import logging
from app.api.auth import check_auth
from app.api.models import AndroidNowPlaying
from app.lametric import LaMetric
from app.lametric.models import CONTENT_TYPE
from fastapi.responses import HTMLResponse
from fastapi.concurrency import run_in_threadpool


router = APIRouter()


@router.post("/status")
async def status(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    return LaMetric.queue.put_nowait((CONTENT_TYPE.LIVESCOREEVENT, payload))


@router.put("/nowplaying")
async def nowplaying(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    android_frame = AndroidNowPlaying.from_request(payload)
    frame = await run_in_threadpool(android_frame.get_frame)
    logging.info(frame)
    return LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, frame.model_dump()))


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
