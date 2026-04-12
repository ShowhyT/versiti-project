from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = ""

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_set(cls, v: str) -> str:
        if not v or len(v) < 16:
            raise ValueError(
                "JWT_SECRET must be configured and at least 16 characters long"
            )
        return v
    webapp_url: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/mirea.db"
    api_bind_host: str = "0.0.0.0"
    api_port: int = 8080
    mirea_proxy: str | None = None
    session_keys: str | None = None
    attendance_max_concurrent: int = 60
    attendance_max_rps: float = 25.0
    attendance_queue_timeout_s: float = 55.0
    attendance_per_request_concurrent: int = 8
    attendance_core_enabled: bool = False
    attendance_core_shadow: bool = True
    attendance_core_bin: str = "./attendance_core/attendance_core_cpp"
    attendance_core_timeout_s: float = 1.2
    health_details_token: str | None = None
    redis_url: str | None = None
    worker_count: int = 1
    feature_grades_enabled: bool = True
    feature_acs_enabled: bool = True
    feature_schedule_enabled: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
