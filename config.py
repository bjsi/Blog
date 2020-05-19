import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    FLASK_DEBUG = False
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
