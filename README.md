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

[buymecoffee]: https://www.buymeacoffee.com/JohNan
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/JohNan/home-assistant-flichub.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40JohNan-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/JohNan/home-assistant-flichub.svg?style=for-the-badge
[releases]: https://github.com/JohNan/home-assistant-flichub/releases
[user_profile]: https://github.com/JohNan