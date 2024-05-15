"""
This module combines all API blueprints into a single Flask app instance.
"""

import datetime
from flask_cors import CORS
from flask_compress import Compress

from flask_openapi3 import Info
from flask_openapi3 import OpenAPI
from flask_jwt_extended import JWTManager
from app.config import UserConfig

from app.settings import Info as AppInfo
from .plugins import lyrics as lyrics_plugin
from app.db.sqlite.auth import SQLiteAuthMethods as authdb
from app.api import (
    album,
    artist,
    colors,
    favorites,
    folder,
    imgserver,
    playlist,
    search,
    settings,
    lyrics,
    plugins,
    logger,
    home,
    getall,
    auth,
    stream,
)

# TODO: Move this description to a separate file
open_api_description = f"""
The REST API exposed by your Swing Music server

### Definition of terms:

#### 1. `limit`: The number of items to return.

In endpoints that request multiple lists of items, this represents the number of items to return for each list.

#### Other infos

- In the folders endpoint, you can request `'$home'` to get the root directories.
---

[MIT License](https://github.com/swing-opensource/swingmusic?tab=MIT-1-ov-file#MIT-1-ov-file) | Copyright (c) {datetime.datetime.now().year} [Mungai Njoroge](https://mungai.vercel.app)
"""


def create_api():
    """
    Creates the Flask instance, registers modules and registers all the API blueprints.
    """
    api_info = Info(
        title=f"Swing Music",
        version=f"v{AppInfo.SWINGMUSIC_APP_VERSION}",
        description=open_api_description,
    )

    app = OpenAPI(__name__, info=api_info, doc_prefix="/docs")
    # JWT CONFIGS
    app.config["JWT_SECRET_KEY"] = UserConfig().userId
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JWT_SESSION_COOKIE"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(datetime.timedelta(days=30).total_seconds())

    # CORS
    CORS(app, origins="*", supports_credentials=True)

    # RESPONSE COMPRESSION
    Compress(app)
    app.config["COMPRESS_MIMETYPES"] = [
        "application/json",
    ]

    # JWT
    jwt = JWTManager(app)

    # @jwt.user_identity_loader
    # def user_identity_lookup(user):
    #     return user

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        userid = identity["id"]
        user = authdb.get_user_by_id(userid)
        return user.todict()

    # Register all the API blueprints
    with app.app_context():
        app.register_api(album.api)
        app.register_api(artist.api)
        app.register_api(stream.api)
        app.register_api(search.api)
        app.register_api(folder.api)
        app.register_api(playlist.api)
        app.register_api(favorites.api)
        app.register_api(imgserver.api)
        app.register_api(settings.api)
        app.register_api(colors.api)
        app.register_api(lyrics.api)

        # Plugins
        app.register_api(plugins.api)
        app.register_api(lyrics_plugin.api)

        # Logger
        app.register_api(logger.api)

        # Home
        app.register_api(home.api)
        app.register_api(getall.api)

        # Auth
        app.register_api(auth.api)

        return app
