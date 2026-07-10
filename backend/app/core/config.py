from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    PROJECT_NAME: str = "DevPilot AI"

    VERSION: str = "1.0.0"

    API_PREFIX: str = "/api/v1"

    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    
    SUPABASE_URL: str

    SUPABASE_JWT_SECRET: str
    
    SUPABASE_KEY: str


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()