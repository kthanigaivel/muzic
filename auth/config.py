from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://muzic_user:gateless@192.168.1.95:5432/muzic"
    SECRET_KEY: str = "Um0EWdzOttS9-yFShwUpXEmvnV0Rkbe1VF6K4GYHrLS5J1xxca7Jc1Vycj1PPABCfq0kCKtwthanigaivel"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file="/etc/muzic/.env"
    )
    

settings = Settings()