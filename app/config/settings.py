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
    OLLAMA_MODEL: str = "phi3:mini"
    OLLAMA_TIMEOUT_SECONDS: int = 300
    LLM_FALLBACK_PROVIDER: str = "groq"
    LLM_FALLBACK_API_KEY: str = ""

    # Hypothesis thresholds
    NOVELTY_THRESHOLD: float = 0.6
    FEASIBILITY_THRESHOLD: float = 0.5

    # Extraction
    EXTRACTION_BATCH_SIZE: int = 10

    # Phase 3: Debate
    DEBATE_MAX_ROUNDS: int = 3
    DEBATE_NOVELTY_MIN: float = 0.6
    DEBATE_FEASIBILITY_MIN: float = 0.5

    # Phase 3: Execution Sandbox
    SANDBOX_CPU_LIMIT: str = "2.0"
    SANDBOX_MEMORY_LIMIT: str = "4g"
    SANDBOX_TIMEOUT_SECONDS: int = 3600
    EXPERIMENT_OUTPUT_DIR: str = "./experiments"

    # Phase 3: Tracking
    WANDB_API_KEY: str = ""
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    RESULTS_BACKEND: str = "local"  # "wandb" | "mlflow" | "local"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
