from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    simulate: bool = False

    led_pin: Optional[int]

    class Config:
        env_file = ".env"

    def __hash__(self):
        return hash((self.simulate, self.led_pin))


@lru_cache()
def get_settings() -> Settings:
    return Settings()