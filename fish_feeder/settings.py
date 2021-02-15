from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    simulate: bool = False

    class Config:
        env_file = ".env"

    def __hash__(self):
        return hash(self.simulate)


@lru_cache()
def get_settings() -> Settings:
    return Settings()