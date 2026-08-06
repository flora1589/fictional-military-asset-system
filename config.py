import os
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    PROJECT_NAME: str = "Military Asset Request & Mission Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "DEFENSE_LOGISTICS_DEFCON1_SECRET_KEY_SUPER_SECURE_JWT_TOKEN_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # SQLite default, easily overridable to PostgreSQL via env var DATABASE_URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./military_assets.db")
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")
settings = Settings()
