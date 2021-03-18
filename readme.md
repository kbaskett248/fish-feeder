# Fish Feeder 5000

This is a project for a Raspberry Pi-based fish feeder. The feeder provides a web-based UI that allows you to feed the fish at the touch of a button.

## Features

### Web-based Frontend

The web-based frontend is powered by [FastAPI](https://github.com/tiangolo/fastapi) and [Jinja](https://github.com/pallets/jinja). In addition to feeding the fish, you can view a log of when the fish was fed.

### Scheduling

With the web-based frontend you can schedule daily feedings. This functionality is powered by [APScheduler](https://github.com/agronholm/apscheduler).

### REST API

The software also offers a REST API, so you can interface with the device from other web-connected devices.

## Materials

* Raspberry Pi 3 B+: $35.00
    * It might run on the Raspberry Pi 3A+ or Zero Wireless.
* 28BYJ-48 Stepper motor and control board: $3.40
* M3 hardware: $0.32
