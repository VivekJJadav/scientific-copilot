from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/scientific_copilot"
    ARXIV_QUERY: str = "transformer reinforcement learning"
    ARXIV_MAX_RESULTS: int = 2
    LOG_LEVEL: str = "INFO"
    MAX_COMPUTE: str = "single_gpu_8gb"
    RELEVANCE_THRESHOLD: float = 0.6

    # Auth
    API_USER: str = "admin"
    API_PASSWORD: str = "password"
    API_KEY: str = "dev-api-key"
    API_RATE_LIMIT_MAX_REQUESTS: int = 30
    API_RATE_LIMIT_WINDOW_SECONDS: int = 60
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # LLM / Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT_SECONDS: int = 600
    LLM_FALLBACK_PROVIDER: str = "groq"
    LLM_FALLBACK_API_KEY: str = ""

    # Hypothesis thresholds
    NOVELTY_THRESHOLD: float = 0.3
    FEASIBILITY_THRESHOLD: float = 0.3

    # Extraction
    EXTRACTION_BATCH_SIZE: int = 5

    # Phase 3: Debate
    DEBATE_MAX_ROUNDS: int = 3
    DEBATE_MAX_SOURCE_PAPERS: int = 5
    DEBATE_NOVELTY_MIN: float = 0.3
    DEBATE_FEASIBILITY_MIN: float = 0.3

    # Phase 3: Execution Sandbox
    SANDBOX_CPU_LIMIT: str = "2.0"
    SANDBOX_MEMORY_LIMIT: str = "4g"
    SANDBOX_TIMEOUT_SECONDS: int = 3600
    EXPERIMENT_OUTPUT_DIR: str = "./experiments"

    # Phase 3: Tracking
    WANDB_API_KEY: str = ""
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    RESULTS_BACKEND: str = "local"  # "wandb" | "mlflow" | "local"

    # Phase 4: Feedback Loop & Clustering
    HDBSCAN_MIN_CLUSTER_SIZE: int = 3
    HDBSCAN_MIN_SAMPLES: int = 2
    GAP_SIMILARITY_THRESHOLD: float = 0.75
    FEEDBACK_MIN_EXPERIMENTS: int = 1
    ARBITER_FEW_SHOT_LIMIT: int = 5
    DATASET_MIN_MENTIONS: int = 2

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return value
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

settings = Settings()
