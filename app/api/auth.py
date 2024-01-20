from app.core.otp import OTP
from app.config import Config as app_config
from fastapi.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN


class Authorization:
    async def __call__(self, request: Request):
        client = request.client
        assert client
        device = request.headers.get("x-device", "")
        if device in app_config.api.device:
            return
        code = request.headers.get("x-totp", "")
        if not OTP.api.verify(code):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )


check_auth = Authorization()
