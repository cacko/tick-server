from bottle import request, HTTPError
from app.core.otp import OTP
from functools import wraps


def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        code = request.get_header("x-totp", "")
        if not OTP.api.verify(code):
            err = HTTPError(403, "no")
            return err
        return f(*args, **kwargs)
    return decorated_function
