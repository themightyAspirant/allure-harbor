from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ALLURE_HARBOR_",
        env_file=".env",
        extra="ignore",
    )

    data_dir: Path = Path("./data")
    max_upload_mb: int = Field(default=200, ge=1)
    max_zip_files: int = Field(default=10000, ge=1)
    max_uncompressed_mb: int = Field(default=1000, ge=1)
    allure_bin: str = "allure"
    allure_timeout_seconds: int = Field(default=300, ge=1)
    public_base_url: str = "http://localhost:8000"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @computed_field  # type: ignore[prop-decorator]
    @property
    def max_uncompressed_bytes(self) -> int:
        return self.max_uncompressed_mb * 1024 * 1024

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        db_path = (self.data_dir / "harbor.db").resolve()
        return "sqlite:///" + db_path.as_posix()
