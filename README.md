# Flic Hub

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

## Prerequisites

Add the tcp client to Flic Hub found in this repo: https://github.com/JohNan/pyflichub-tcpclient

### Install with HACS (recommended)
Add the url to the repository as a custom integration.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `flichub`.
4. Download _all_ the files from the `custom_components/flichub/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Flic Hub"

### DHCP Discovery
Your FlicHub should automatically be discovered as a new integration based on dhcp discovery.
If that doesn't work it can be setup manually by doing step 7 in the installation instructions

## Using the Flic Twist dial

A Twist's rotation only works once it's bound to a **virtual device** — otherwise turning it does nothing. In the Flic app: open the Twist → its **Rotate** action → pick what to control (Brightness, Volume, etc.) → **add devices** → **Flic Hub Studio** → **add a virtual device** (Light/Speaker/Blind) → give it a name → confirm it's assigned to Rotate.

Once set up, turning the dial drives a matching entity in Home Assistant (e.g. `light.living_room_twist_ha_lamp_dial`) in real time — read its state in an automation to control anything else.

[buymecoffee]: https://www.buymeacoffee.com/JohNan
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/JohNan/home-assistant-flichub.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40JohNan-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/JohNan/home-assistant-flichub.svg?style=for-the-badge
[releases]: https://github.com/JohNan/home-assistant-flichub/releases
[user_profile]: https://github.com/JohNan
