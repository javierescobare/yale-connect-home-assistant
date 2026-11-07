# Publishing a version

## GitHub repository

- Name: `yale-connect-home-assistant`.
- Suggested description: `Unofficial Yale Connect integration for Home Assistant with lock control, status monitoring, and access events.`
- Public visibility for HACS installation.
- Issues enabled.
- Suggested topics: `home-assistant`, `hacs`, `yale`, `yale-connect`, `smart-lock`.
- Enable private vulnerability reporting if that channel will be used.

The tested installation is in Peru. This does not establish a geographic restriction. Do not add compatibility claims without testing the model and account.

## Validate a version

1. Run tests, Ruff, and `scripts/validate_repository.py`.
2. Check the hassfest and HACS results in GitHub Actions.
3. Inspect the commit contents: no HA configuration, backups, caches, or personal data. `.gitignore` does not protect files already tracked by Git.
4. Update `manifest.json`, `CHANGELOG.md`, and limitations as needed.
5. Create a GitHub release with a tag and version matching the manifest. Mark the initial publication as a **pre-release** because it is a beta.

A tag alone does not make a HACS release. Distribution currently uses the files under `custom_components/yale_connect/`, without a special release ZIP. Inclusion in the default HACS catalog is a separate process and has not been requested.

## Changes and tests in a real installation

Keep a backup before replacing integration files, and restart Home Assistant Core to load Python changes. Reloading an integration is not a substitute for this restart. Verify that the entry loads, entities appear, and options retain their values. Automated tests must never use real credentials or operate a lock.
