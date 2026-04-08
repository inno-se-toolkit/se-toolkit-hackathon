"""Configuration for the bot."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Config:
    bot_token: Optional[str] = None
    backend_api_url: Optional[str] = None
    backend_api_key: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_api_base_url: Optional[str] = None
    llm_api_model: Optional[str] = None

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        if env_file:
            path = Path(env_file)
            if path.exists():
                with open(path) as f:
                    for line in f:
                        line=line.strip()
                        if not line or line.startswith("#"): continue
                        if "=" in line:
                            k,v=line.split("=",1); os.environ.setdefault(k.strip(),v.strip())
        return cls(
            bot_token=os.getenv("BOT_TOKEN"),
            backend_api_url=os.getenv("BACKEND_API_URL") or os.getenv("LMS_API_BASE_URL"),
            backend_api_key=os.getenv("BACKEND_API_KEY") or os.getenv("LMS_API_KEY"),
            llm_api_key=os.getenv("LLM_API_KEY"),
            llm_api_base_url=os.getenv("LLM_API_BASE_URL"),
            llm_api_model=os.getenv("LLM_API_MODEL"),
        )

def load_config(require_bot_token: bool = True) -> Config:
    bot_dir = Path(__file__).parent
    for name in [".env.bot.secret", ".env.bot", ".env"]:
        p = bot_dir / name
        if p.exists():
            return Config.from_env(str(p))
    return Config.from_env()
