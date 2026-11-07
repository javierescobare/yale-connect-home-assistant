# Yale Connect for Home Assistant

Unofficial Yale Connect integration for Home Assistant with lock control, status monitoring, and access events.

**Status: beta (`0.1.0`).** Lock control has been tested in a real installation. Access history and activity events are experimental and have [known limitations](docs/limitations.md).

This is an independent project, not affiliated with Yale or ASSA ABLOY.

## Compatibility

This integration uses your **Yale Connect app** account and its cloud service at `api.connectservices.assaabloy.com/api/YaleConnect`.

Yale Home, Yale Access, and August use different platforms. An accessory named "Yale Connect Wi-Fi Bridge" does not establish compatibility: check which app and account you use. This component does not implement the Yale Home/August APIs.

| Validation | Environment |
| --- | --- |
| Real installation | Yale **YDM 60**, Yale Connect account, Peru |
| Real Home Assistant installation | **2026.11.0** |
| Automated tests | Home Assistant **2026.10.4**, Python **3.14** |

Other models, countries, and account configurations have not been verified. Peru is the location of the tested installation, not a geographic restriction of this project. Compatibility reports are welcome.

## Features

- Lock entity: lock, monitor state, and optionally unlock.
- Connectivity and low-battery indicators, when reported by the device.
- Last known unlock sensor, including user, method, and time when available.
- Activity event entity with `locked`, `unlocked`, and `unknown` events.
- UI setup, options, and account reauthentication.

Cloud polling is scheduled every **20 seconds**. Updates are not instantaneous; additional refreshes are requested after a command. An accepted API command does not guarantee that the physical lock completed the operation.

## Installation

You need Home Assistant 2026.10.4 or later, a Yale Connect account, and a lock accessible through that app, typically through its internet-connected hub.

### HACS: custom repository

This project is distributed as a custom repository. This does not imply inclusion in the default HACS catalog.

1. In HACS, open **Custom repositories** from its menu.
2. Add `https://github.com/javierescobare/yale-connect-home-assistant` as an **Integration**.
3. Download **Yale Connect**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration → Yale Connect**.

### Manual installation

1. Download this repository's source code.
2. Copy only `custom_components/yale_connect/` into `<config>/custom_components/yale_connect/` in your Home Assistant installation.
3. Restart Home Assistant and add **Yale Connect** through the UI.

To update, back up the previous integration directory, replace its code, and restart Home Assistant Core. Reloading an integration does not reload its Python modules.

## Configuration and PIN

Use the email and password of your Yale Connect account. The entry PIN is sent to the Yale cloud when requesting a lock or unlock operation.

**Unlocking is disabled by default.** Explicitly enable it in the integration's options if desired. While disabled, the unlock method rejects the action before sending a command to Yale.

The PIN is configured once per account and reused for its locks. There is no per-device PIN setting. Home Assistant does not ask for a fresh PIN on each action: when unlocking is enabled, authorized HA actions can use the stored PIN.

The password and PIN are stored in Home Assistant's locally managed configuration. Masking the form only protects their display; it does not encrypt configuration files. Treat HA configuration and backups as sensitive. Activity attributes may include names and timestamps that Home Assistant can retain in its history.

## Known limitations

- Different records for the same device and timestamp may produce only one event.
- Records after the previous day's last poll may be missed at midnight.
- Late-arriving records older than the last observed timestamp may also be skipped.
- Parsing still assumes parts of Yale's response structure.
- The last unlock is reconstructed from the current day's records, not a complete persistent history.
- Devices are discovered during setup. Reload the integration after adding a device in Yale.
- Entity names are fixed in English; setup forms have English and Spanish translations.

See [details and pending work](docs/limitations.md). Events are not a complete audit log and should not be the sole condition for automations that unlock a door.

## Tests and contributions

Tests use an isolated Home Assistant instance, fictional credentials, and simulated responses. Network connections are blocked by the pytest configuration. You do not need a Yale account or a physical lock to run them.

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_repository.py
```

GitHub Actions runs these checks and includes hassfest and HACS validation jobs. See [CONTRIBUTING.md](CONTRIBUTING.md) to propose changes and [SECURITY.md](SECURITY.md) to report sensitive issues.

## License

[MIT](LICENSE). The included generic icon is original project artwork, not an official Yale logo. Product names and trademarks belong to their respective owners.
