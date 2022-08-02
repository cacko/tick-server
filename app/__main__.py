

import logging
from app.core.app import App

try:
    App.start()
except KeyboardInterrupt:
    import sys
    sys.exit(0)
except Exception as e:
    logging.exception(e, exc_info=True)
