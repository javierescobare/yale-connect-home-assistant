# Changelog

## 0.1.0 — initial public beta

- Yale Connect cloud integration with lock, connectivity, low battery, last-unlock, and activity-event entities.
- UI configuration, options, and account reauthentication.
- Unlocking disabled by default and PIN masking in forms.
- HTTP 429 and 5xx treated as temporary failures, and command errors without the Yale response body.
- Safe cancellation of pending operations when a device disappears.
- Regression tests, CI configuration, and documented limitations.

Access history and events remain experimental. See [known limitations](docs/limitations.md).
