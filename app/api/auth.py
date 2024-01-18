import logging
from bottle import request, HTTPError
from app.core.otp import OTP
from functools import wraps
from app.config import Config as app_config


def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        code = request.get_header("x-totp", "")
        device = request.get_header("x-device", "")
        logging.info(f"device id = {device}")
        if not any([OTP.api.verify(code), device in app_config.api.device]):
            err = HTTPError(403, "no")
            return err
        return f(*args, **kwargs)
    return decorated_function
