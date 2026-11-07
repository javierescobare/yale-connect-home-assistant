# Security

Version `0.1.0` is a beta. This component controls a lock and handles Yale Connect account credentials, an optional PIN, and activity data.

## Reporting a sensitive issue

Use **Security → Report a vulnerability** on GitHub if private vulnerability reporting is enabled for the repository. If it is unavailable, open an issue requesting a private contact channel without publishing vulnerability details or access information. The project does not guarantee a response time.

Include the version, impact, and reproduction steps using fictional information. Never attach credentials, Home Assistant backups, or unredacted access logs.

## Relevant behavior

- Unlocking from HA is disabled by default and checked in the action method.
- Once enabled, authorized HA actions can use the saved PIN; it is not required again on each call.
- Forms mask the PIN. This does not encrypt configuration files or replace protection of HA backups and permissions.
- Yale requests use HTTPS with default TLS certificate verification.
- Command errors do not include the server response body.
- Activity can include names and timestamps, and entities may be stored by Home Assistant's Recorder.

The [history limitations](docs/limitations.md) prevent treating it as a complete audit log. The available review and tests are not an independent security audit.
