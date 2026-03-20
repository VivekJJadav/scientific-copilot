from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/scientific_copilot"
    ARXIV_QUERY: str = "transformer reinforcement learning"
    ARXIV_MAX_RESULTS: int = 10
    LOG_LEVEL: str = "INFO"
    MAX_COMPUTE: str = "single_gpu_8gb"
    RELEVANCE_THRESHOLD: float = 0.6

    # LLM / Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_TIMEOUT_SECONDS: int = 30
    LLM_FALLBACK_PROVIDER: str = "groq"
    LLM_FALLBACK_API_KEY: str = ""

    # Hypothesis thresholds
    NOVELTY_THRESHOLD: float = 0.6
    FEASIBILITY_THRESHOLD: float = 0.5

    # Extraction
    EXTRACTION_BATCH_SIZE: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
