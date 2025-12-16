from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    API_SECRET_KEY: str = "supersecretkey"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Bot Config (Optional for Backend, but present in .env)
    DISCORD_TOKEN: str = ""
    TARGET_CHANNELS: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
