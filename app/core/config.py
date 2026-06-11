import os
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=False)


def _parameter_to_env_name(name: str, prefix: str) -> str:
    relative_name = name.removeprefix(prefix).strip("/")
    leaf_name = relative_name.split("/")[-1]
    return leaf_name.replace("-", "_").upper()


def load_ssm_parameters() -> None:
    source = os.getenv("APP_CONFIG_SOURCE", "env").strip().lower()
    prefix = os.getenv("APP_SSM_PREFIX", "").strip().rstrip("/")

    if source != "ssm" and not prefix:
        return

    if not prefix:
        raise RuntimeError("APP_SSM_PREFIX is required when APP_CONFIG_SOURCE=ssm")

    region_name = os.getenv("AWS_REGION", "us-east-1")
    client = boto3.client("ssm", region_name=region_name)

    try:
        paginator = client.get_paginator("get_parameters_by_path")
        for page in paginator.paginate(
            Path=prefix,
            Recursive=True,
            WithDecryption=True,
        ):
            for parameter in page.get("Parameters", []):
                env_name = _parameter_to_env_name(parameter["Name"], prefix)
                value = parameter.get("Value")
                if value is not None and not os.getenv(env_name):
                    os.environ[env_name] = value
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        raise RuntimeError(
            f"Failed to load SSM parameters from {prefix}: {error_code}"
        ) from exc


class Settings(BaseSettings):
    app_name: str = "FastAPI Serverless Lambda"
    stage: str = "dev"
    app_config_source: str = "env"
    app_ssm_prefix: str | None = None
    log_level: str = "INFO"
    aws_region: str = "us-east-1"
    cors_allow_origins: str = "*"
    nlp_conversation_queue_url: str | None = None
    connections_table: str | None = None
    ws_endpoint: str | None = None
    openai_api_key: str | None = None
    openai_default_model: str = "gpt-5.5"
    openai_embedding_model: str = "text-embedding-3-large"
    anthropic_api_key: str | None = None
    anthropic_default_model: str | None = None
    milvus_uri: str | None = None
    milvus_token: str | None = None
    milvus_username: str | None = None
    milvus_password: str | None = None
    milvus_collection_name: str = "rag_documents"
    milvus_embedding_dim: int = 3072

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [
            origin.strip()
            for origin in self.cors_allow_origins.split(",")
            if origin.strip()
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_ssm_parameters()
    return Settings()
