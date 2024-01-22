from pathlib import Path
from fastapi import APIRouter, Depends, Request
import logging
from app.api.auth import check_auth
from app.api.models import AndroidNowPlaying
from app.lametric import LaMetric
from app.lametric.models import CONTENT_TYPE, MUSIC_STATUS
from fastapi.responses import HTMLResponse
from fastapi.concurrency import run_in_threadpool


router = APIRouter(prefix="/api")


@router.post("/status")
async def status(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    return LaMetric.queue.put_nowait((CONTENT_TYPE.LIVESCOREEVENT, payload))


@router.put("/nowplaying")
async def nowplaying(request: Request, auth=Depends(check_auth)):
    try:
        payload = await request.json()
        logging.debug(payload)
        android_frame = AndroidNowPlaying.from_request(payload)
        frame = await run_in_threadpool(android_frame.get_frame)
        return LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, frame.model_dump()))
    except Exception as e:
        logging.exception(e)
        return LaMetric.queue.put_nowait((CONTENT_TYPE.YANKOSTATUS, dict(status=MUSIC_STATUS.STOPPED.value)))


@router.post("/nowplaying")
async def post_nowplaying(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    logging.debug(payload)
    return LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, payload))

@router.put("/playstatus")
async def put_playingstatus(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    logging.debug(payload)
    return LaMetric.queue.put_nowait((CONTENT_TYPE.YANKOSTATUS, payload.get("status", "stopped")))



@router.post("/subscription")
async def on_subscription(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    return LaMetric.queue.put_nowait((CONTENT_TYPE.LIVESCOREEVENT, payload))


@router.get("/privacy", response_class=HTMLResponse)
async def privacy():
    html_path = Path(__file__).parent / "views" / "privacy.tpl"
    return html_path.read_text()
