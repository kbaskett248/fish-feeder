from time import sleep

from gpiozero import LED
from pydantic import BaseModel
from pydantic.decorator import validate_arguments


class PinSpec(BaseModel):
    led_pin: int


class Device:
    led: LED

    @validate_arguments
    def __init__(self, pins: PinSpec):
        self.led = LED(pins.led_pin)

    def pulse_led(self):
        self.led.on()
        sleep(2.5)
        self.led.off()
