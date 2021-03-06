from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi.params import File
from pydantic import BaseSettings


class Settings(BaseSettings):
    simulate: bool = False
    db_path: Path = Path("./fish-feeder.db")

    led_pin: Optional[int]

    motor_pin_1: Optional[int]
    motor_pin_2: Optional[int]
    motor_pin_3: Optional[int]
    motor_pin_4: Optional[int]

    class Config:
        env_file = ".env"

    def __hash__(self):
        return hash((self.simulate, self.led_pin, self.db_path))

    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
