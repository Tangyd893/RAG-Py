from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 应用
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # 数据库
    postgres_db: str = "rag"
    postgres_user: str = "rag"
    postgres_password: str = "rag"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    database_url: str = "postgresql+asyncpg://rag:rag@postgres:5432/rag"

    # Redis / Celery
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # 向量存储
    vector_store_provider: str = "chroma"
    chroma_host: str = "chroma"
    chroma_port: int = 8000
    chroma_collection: str = "rag_chunks"

    # 嵌入模型
    embedding_provider: str = "bge"
    bge_model_name: str = "BAAI/bge-m3"
    bge_device: str = "cpu"

    # LLM
    llm_provider: str = "mimo"
    mimo_base_url: str = ""
    mimo_model: str = "mimo-chat"
    mimo_api_key: str = ""
    mimo_timeout_seconds: int = 60

    # 存储
    storage_provider: str = "local"
    local_storage_path: str = "./data/files"


settings = Settings()
