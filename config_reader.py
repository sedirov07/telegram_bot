from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    """Configuration settings for the bot."""

    bot_token: SecretStr

    class Config:
        """Additional configuration options for the settings."""

        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Settings()
