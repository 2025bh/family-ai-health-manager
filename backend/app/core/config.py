from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """集中管理配置；缺少外部密钥时自动使用 Mock。"""

    app_name: str = "家医 · 家庭健康管家"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/familycare.db"
    frontend_origin: str = "http://localhost:5173"
    upload_dir: str = "./data/uploads"
    llm_provider: str = "mock"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    feishu_provider: str = "mock"
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_base_token: str = ""
    feishu_user_access_token: str = ""
    feishu_parent_wiki_token: str = "ZLGKwWARWiXyLvk5enecv1vYnVf"
    phone_provider: str = "mock"
    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    def ensure_directories(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.removeprefix("sqlite:///")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
