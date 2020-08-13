import os
import app.static.avatars as avatars_folder


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "super-duper-cyber-secret"
    # Google Recaptcha
    RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY")
    RECAPTCHA_PRIVATE_KEY = os.getenv("RECAPTCHA_PRIVATE_KEY")
    # Auto generated avatars
    AVATARS_SAVE_PATH = os.path.dirname(avatars_folder.__file__)
    AVATARS_IDENTICON_ROWS = 7
    AVATARS_IDENTICON_COLS = 7
    AVATARS_IDENTICON_BG = (125, 125, 125)
    AVATARS_SIZE_TUPLE = (30, 60, 150)
    AVATARS_CROP_BASE_WIDTH = 500
    AVATARS_CROP_INIT_POS = (0, 0)
    AVATARS_SERVE_LOCAL = False



    # Basic Auth
    BASIC_AUTH_USERNAME = os.getenv("BASIC_AUTH_USERNAME")
    BASIC_AUTH_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")

    # Logging
    FLASK_LOG_LEVEL = 'WARNING'

