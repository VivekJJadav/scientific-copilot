from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/scientific_copilot"
    ARXIV_QUERY: str = "transformer reinforcement learning"
    ARXIV_MAX_RESULTS: int = 10
    LOG_LEVEL: str = "INFO"
    MAX_COMPUTE: str = "single_gpu_8gb"
    RELEVANCE_THRESHOLD: float = 0.6

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
