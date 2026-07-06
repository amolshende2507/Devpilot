from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    PROJECT_NAME: str = "DevPilot AI"

    VERSION: str = "1.0.0"

    API_PREFIX: str = "/api/v1"

    ENVIRONMENT: str = "development"


    class Config:
        env_file = ".env"



settings = Settings()