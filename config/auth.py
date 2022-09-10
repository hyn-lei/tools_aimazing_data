from pydantic import BaseSettings


class Settings(BaseSettings):
    JWT_TTL: int = 60 * 24 * 8
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = 'HS256'


settings = Settings()