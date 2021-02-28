from enum import Enum
from time import sleep
from typing import Iterable, Sequence, Tuple

from gpiozero import LED, OutputDevice
from loguru import logger
from pydantic import BaseModel
from pydantic.decorator import validate_arguments


class PinSpec(BaseModel):
    led_pin: int
    motor_pin_1: int
    motor_pin_2: int
    motor_pin_3: int
    motor_pin_4: int


class DRV8825:
    """Don't think I can use this because it's intended to drive bipolar stepper motors."""

    class Direction(Enum):
        FORWARD = 0
        REVERSE = 1

    class Mode(Enum):
        HARDWARE = 0
        SOFTWARE = 1

    class StepFormat(Enum):
        FULL = (0, 0, 0)
        HALF = (1, 0, 0)
        QUARTER = (0, 1, 0)
        EIGHTH = (1, 1, 0)
        SIXTEENTH = (0, 0, 1)
        THIRTY_SECOND = (1, 0, 1)

    def __init__(
        self, dir_pin: int, step_pin: int, enable_pin: int, mode_pins: Tuple[int]
    ):
        self.dir_pin = OutputDevice(dir_pin)
        self.step_pin = OutputDevice(step_pin)
        self.enable_pin = OutputDevice(enable_pin)
        self.mode_pins = [OutputDevice(pin) for pin in mode_pins]

    def stop(self):
        self.enable_pin.on()

    def set_step_format(self, mode: "DRV8825.Mode", step_format: "DRV8825.StepFormat"):
        logger.debug("Motor control mode: {}", mode)
        if mode == self.Mode.SOFTWARE:
            logger.debug("Setting pins")
            for pin, state in zip(self.mode_pins, step_format.value):
                if state == 1:
                    pin.on()
                else:
                    pin.off()

    def turn(
        self, direction: "DRV8825.Direction", steps: int, step_delay: float = 0.005
    ):
        if direction == self.Direction.FORWARD:
            logger.debug("Forward: {} steps", steps)
            self.enable_pin.off()
            self.dir_pin.off()
        elif direction == self.Direction.REVERSE:
            logger.debug("Reverse: {} steps", steps)
            self.enable_pin.off()
            self.dir_pin.on()
        else:
            logger.warning("Invalid direction: {}", direction)
            self.enable_pin.on()
            return

        if steps == 0:
            return

        for _ in range(steps):
            self.step_pin.on()
            sleep(step_delay)
            self.step_pin.off()
            sleep(step_delay)

    @classmethod
    def get_motor_1(cls) -> "DRV8825":
        return cls(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))

    @classmethod
    def get_motor_2(cls) -> "DRV8825":
        return cls(dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))


class StepperMotorInUseException(Exception):
    motor: "StepperMotor"

    def __init__(self, motor: "StepperMotor") -> None:
        super().__init__()
        self.motor = motor

    def __str__(self) -> str:
        return "Stepper motor already in use"


PartialStep = Tuple[int, int, int, int]


class StepperMotor:
    """A stepper motor controller class."""

    sequence: Sequence[PartialStep] = (
        (0, 0, 0, 1),
        (0, 0, 1, 1),
        (0, 0, 1, 0),
        (0, 1, 1, 0),
        (0, 1, 0, 0),
        (1, 1, 0, 0),
        (1, 0, 0, 0),
        (1, 0, 0, 1),
    )
    steps_per_revolution = 512
    turning: bool

    def __init__(self, pin1: int, pin2: int, pin3: int, pin4: int) -> None:
        self.pins = [OutputDevice(pin) for pin in (pin1, pin2, pin3, pin4)]
        self.turning = False

    def turn_angle(self, angle: float, step_delay: float = 0.005) -> None:
        if self.turning:
            raise StepperMotorInUseException(self)

        self.turning = True

        if angle == 0:
            logger.warning("Requested 0 degree trun")
            return
        steps = round(abs(angle) / 360 * 512)
        logger.debug("Turning {} steps")
        method = self.step_clockwise if angle > 0 else self.step_counter_clockwise
        for _ in range(steps):
            method(step_delay)

        self.turning = False

    def step_clockwise(self, time_delay: float = 0.005) -> None:
        self._step(self.sequence, time_delay)

    def step_counter_clockwise(self, time_delay: float = 0.005) -> None:
        self._step(reversed(self.sequence), time_delay)

    def _step(self, sequence: Iterable[PartialStep], time_delay: float = 0.005) -> None:
        for partial_step in sequence:
            for command, pin in zip(partial_step, self.pins):
                if command == 1:
                    pin.on()
                else:
                    pin.off()

            sleep(time_delay)


class Device:
    led: LED
    motor: StepperMotor

    @validate_arguments
    def __init__(self, pins: PinSpec):
        self.led = LED(pins.led_pin)
        self.motor = StepperMotor(
            pins.motor_pin_1, pins.motor_pin_2, pins.motor_pin_3, pins.motor_pin_4
        )

    def pulse_led(self):
        self.led.on()
        sleep(2.5)
        self.led.off()

    def turn_motor(self, angle: float) -> None:
        self.motor.turn_angle(angle)
