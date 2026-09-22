"""Actra configuration — loaded from environment / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _find_env_file() -> Path | None:
    """Walk up from CWD looking for a .env file."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    return None


@dataclass(frozen=True)
class Settings:
    """Immutable application settings for local Actra."""

    # Local LLM (Ollama)
    ollama_host: str = "http://localhost:11434"
    model_name: str = "gemma4:12b-mlx"
    num_ctx: int = 8192

    # Agent behaviour
    max_retries: int = 3
    require_confirmation: bool = True
    no_confirm: str = "none"  # "none", "sensitive", "all"
    log_level: str = "INFO"

    # Paths
    log_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")
    screenshot_dir: Path = field(
        default_factory=lambda: Path.cwd() / "screenshots"
    )
    memory_db_path: Path = field(
        default_factory=lambda: Path.home() / ".actra" / "memory.db"
    )

    @classmethod
    def load(cls) -> Settings:
        """Load settings from environment variables (with .env fallback)."""
        env_file = _find_env_file()
        if env_file:
            load_dotenv(env_file)

        no_confirm_env = os.getenv("ACTRA_NO_CONFIRM")
        req_confirm_env = os.getenv("ACTRA_REQUIRE_CONFIRMATION")
        if no_confirm_env:
            no_confirm_val = no_confirm_env.lower().strip()
            req_confirm_val = (no_confirm_val != "all")
        elif req_confirm_env is not None:
            req_confirm_val = req_confirm_env.lower() == "true"
            no_confirm_val = "none" if req_confirm_val else "all"
        else:
            no_confirm_val = "none"
            req_confirm_val = True

        mem_path_env = os.getenv("ACTRA_MEMORY_DB_PATH")
        mem_path = Path(mem_path_env).expanduser() if mem_path_env else (Path.home() / ".actra" / "memory.db")

        return cls(
            ollama_host=os.getenv("ACTRA_OLLAMA_HOST", "http://localhost:11434"),
            model_name=os.getenv("ACTRA_MODEL_NAME", "gemma4:12b-mlx"),
            num_ctx=int(os.getenv("ACTRA_NUM_CTX", "8192")),
            max_retries=int(os.getenv("ACTRA_MAX_RETRIES", "3")),
            require_confirmation=req_confirm_val,
            no_confirm=no_confirm_val,
            log_level=os.getenv("ACTRA_LOG_LEVEL", "INFO"),
            memory_db_path=mem_path,
        )
