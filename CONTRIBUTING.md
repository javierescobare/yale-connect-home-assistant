# Contributing

Bug reports, compatibility reports, and pull requests are welcome. Include the device model, exact app used, account country, and HA version when relevant. A product named "Yale Connect" may belong to a different platform.

Write code, comments, documentation, and default UI strings in English. Other languages belong in locale files under `translations/`.

## Local development

Use Python 3.14 and a virtual environment. Install `requirements-dev.txt` and run:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python scripts/validate_repository.py
```

The current test dependency uses Home Assistant 2026.10.4. A real installation has also been checked on 2026.11.0. Update test dependencies explicitly and verify compatibility changes before broadening the requirements.

## Proposing a change

1. Describe the problem with a concrete example and the expected behavior.
2. Fork the repository, create a branch, and keep the change focused.
3. Add a regression test when changing API handling, permissions, commands, or events.
4. Run the checks above and update affected documentation.
5. Open a pull request explaining the change and its validation.

Use simulated responses and fictional data. Never send commands to a real lock from tests or GitHub Actions. Preserve the disabled-by-default unlock setting. Do not retry commands after network failures if you cannot know whether the first request executed.

Read [the history limitations](docs/limitations.md) before changing event handling. Replacing `>` with `>=` is not a deduplication fix: it would replay events on each poll.

## Data and attribution

Do not include passwords, tokens, PINs, email addresses, physical addresses, real identifiers, personal names, or unredacted access records. Replace values with fictional data while preserving the structure needed to reproduce the issue.

If you incorporate another project's code, preserve its license and attribution and explain its origin in the pull request. Contributions are distributed under the project's MIT license.
