from pathlib import Path
from fastapi import APIRouter, Depends, Request, Response
import logging
from app.api.auth import check_auth
from app.api.models import AndroidNowPlaying
from app.lametric import LaMetric
from app.lametric.models import CONTENT_TYPE, MUSIC_STATUS
from fastapi.responses import HTMLResponse
from fastapi.concurrency import run_in_threadpool
from lambo.hue.client import Hue


router = APIRouter(prefix="/api")


@router.post("/status")
async def status(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    return LaMetric.queue.put_nowait((CONTENT_TYPE.LIVESCOREEVENT, payload))


@router.put("/nowplaying")
async def nowplaying(request: Request):
    try:
        payload = await request.json()
        logging.debug(payload)
        android_frame = AndroidNowPlaying.from_request(payload)
        frame = await run_in_threadpool(android_frame.get_frame)
        return LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, frame.model_dump()))
    except Exception as e:
        logging.exception(e)
        return LaMetric.queue.put_nowait(
            (CONTENT_TYPE.YANKOSTATUS, dict(status=MUSIC_STATUS.STOPPED.value))
        )


@router.post("/nowplaying")
async def post_nowplaying(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    logging.debug(payload)
    return LaMetric.queue.put_nowait((CONTENT_TYPE.NOWPLAYING, payload))


@router.get("/playstatus")
async def put_playstatus(status: str = "stopped"):
    return LaMetric.queue.put_nowait(
        (CONTENT_TYPE.YANKOSTATUS, dict(status=status))
    )


@router.post("/subscription")
async def on_subscription(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    return LaMetric.queue.put_nowait((CONTENT_TYPE.LIVESCOREEVENT, payload))


@router.get("/privacy", response_class=HTMLResponse)
async def privacy():
    html_path = Path(__file__).parent / "views" / "privacy.tpl"
    return html_path.read_text()

@router.post("/termo")
async def post_termo(request: Request, auth=Depends(check_auth)):
    payload = await request.json()
    LaMetric.queue.put_nowait((CONTENT_TYPE.TERMO, payload))
    return {"status": "ok"}

@router.post("/sure")
async def post_sure(request: Request):
    payload = await request.json()
    LaMetric.queue.put_nowait((CONTENT_TYPE.SURE, payload))
    return {"status": "ok"}

@router.post("/alert")
async def post_alert(request: Request, auth=Depends(check_auth)):
    Hue.signaling(duration=1000, colors=["DDDD00", "DD1FD0"])
    return {"status": "ok"}