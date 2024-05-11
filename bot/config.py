from os import getenv

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class Settings:
    TG_TOKEN: str = getenv("TG_TOKEN")
    MONGODB_CLIENT_URL: str = getenv("MONGODB_CLIENT_URL")


settings = Settings()
