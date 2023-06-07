import os
import logging

from dotenv import load_dotenv
from quart import Quart

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


def create_app():
    app = Quart(__name__)
    app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY")

    from .views import views
    from .auth import auth
    from .api.channels.main import channels

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(channels, url_prefix="/api/channels")

    import website.connection

    return app
