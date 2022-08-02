from bottle import request, HTTPError
import pyotp
from app.config import Config
from functools import wraps



def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        otp = request.get_header("x-totp", "")
        totp = pyotp.TOTP(Config.api.secret)
        if not totp.verify(otp):
            err = HTTPError(403, "no")
            return err
        return f(*args, **kwargs)
    return decorated_function