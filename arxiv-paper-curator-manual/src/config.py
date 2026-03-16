from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    name: str
    env: str
    port: int


class DatabaseConfig(BaseModel):
    url: str


class ArxivConfig(BaseModel):
    api_url: str
    default_query: str
    default_max_results: int


class OpenSearchConfig(BaseModel):
    url: str
    username: str
    password: str


class OllamaConfig(BaseModel):
    base_url: str
    model: str


class RedisConfig(BaseModel):
    url: str


class EmbeddingsConfig(BaseModel):
    api_key: str
    base_url: str
    model: str
    dimensions: int


class LangfuseConfig(BaseModel):
    enabled: bool
    host: str
    public_key: str
    secret_key: str


class ChunkingConfig(BaseModel):
    chunk_size: int
    overlap: int


class ParserConfig(BaseModel):
    provider: str
    timeout_seconds: int
    user_agent: str


class TelegramConfig(BaseModel):
    enabled: bool
    bot_token: str
    chat_id: str
    api_base_url: str
    poll_interval_seconds: float


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # Legacy flat fields (kept for backward compatibility with existing .env)
    app_name: str = "arxiv-paper-curator-manual"
    app_env: str = "dev"
    app_port: int = 8000

    database_url: str

    arxiv_api_url: str = "https://export.arxiv.org/api/query"
    arxiv_default_query: str = "cat:cs.AI"
    arxiv_default_max_results: int = 5

    opensearch_url: str
    opensearch_username: str = "admin"
    opensearch_password: str = "admin"

    ollama_base_url: str
    ollama_model: str = "llama3.2:3b"

    redis_url: str = "redis://redis:6379/0"

    jina_api_key: str = ""
    jina_base_url: str = "https://api.jina.ai/v1/embeddings"
    jina_embedding_model: str = "jina-embeddings-v3"
    embedding_dimensions: int = 1024

    tracing_enabled: bool = True
    langfuse_host: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    chunk_size: int = 800
    chunk_overlap: int = 120

    parser_provider: str = "docling"
    parser_timeout_seconds: int = 90
    parser_user_agent: str = "arxiv-paper-curator-manual/1.0"

    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_api_base_url: str = "http://127.0.0.1:8000"
    telegram_poll_interval_seconds: float = 2.0

    @model_validator(mode="after")
    def validate_critical_values(self) -> "Settings":
        if not self.database_url.strip():
            raise ValueError("DATABASE_URL must be set")
        if not self.opensearch_url.strip():
            raise ValueError("OPENSEARCH_URL must be set")
        if not self.ollama_base_url.strip():
            raise ValueError("OLLAMA_BASE_URL must be set")
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE must be > 0")
        if self.chunk_overlap < 0:
            raise ValueError("CHUNK_OVERLAP must be >= 0")
        return self

    @property
    def app(self) -> AppConfig:
        return AppConfig(name=self.app_name, env=self.app_env, port=self.app_port)

    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(url=self.database_url)

    @property
    def arxiv(self) -> ArxivConfig:
        return ArxivConfig(
            api_url=self.arxiv_api_url,
            default_query=self.arxiv_default_query,
            default_max_results=self.arxiv_default_max_results,
        )

    @property
    def opensearch(self) -> OpenSearchConfig:
        return OpenSearchConfig(
            url=self.opensearch_url,
            username=self.opensearch_username,
            password=self.opensearch_password,
        )

    @property
    def ollama(self) -> OllamaConfig:
        return OllamaConfig(base_url=self.ollama_base_url, model=self.ollama_model)

    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(url=self.redis_url)

    @property
    def embeddings(self) -> EmbeddingsConfig:
        return EmbeddingsConfig(
            api_key=self.jina_api_key,
            base_url=self.jina_base_url,
            model=self.jina_embedding_model,
            dimensions=self.embedding_dimensions,
        )

    @property
    def langfuse(self) -> LangfuseConfig:
        return LangfuseConfig(
            enabled=self.tracing_enabled,
            host=self.langfuse_host,
            public_key=self.langfuse_public_key,
            secret_key=self.langfuse_secret_key,
        )

    @property
    def chunking(self) -> ChunkingConfig:
        return ChunkingConfig(chunk_size=self.chunk_size, overlap=self.chunk_overlap)

    @property
    def parser(self) -> ParserConfig:
        return ParserConfig(
            provider=self.parser_provider,
            timeout_seconds=self.parser_timeout_seconds,
            user_agent=self.parser_user_agent,
        )

    @property
    def telegram(self) -> TelegramConfig:
        return TelegramConfig(
            enabled=self.telegram_enabled,
            bot_token=self.telegram_bot_token,
            chat_id=self.telegram_chat_id,
            api_base_url=self.telegram_api_base_url,
            poll_interval_seconds=self.telegram_poll_interval_seconds,
        )


settings = Settings()
