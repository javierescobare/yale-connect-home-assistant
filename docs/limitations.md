# Known limitations and pending work

These limitations are present in the initial version. Publishing and documenting them does not mean they have been resolved.

## Records sharing a timestamp

The coordinator keeps the greatest `operationDateTime` observed per device and only emits records with a later timestamp. Different operations sharing a timestamp may therefore collapse into a single event. Late-arriving records with an older timestamp can also be skipped.

A fix requires verifying whether Yale supplies a stable record identifier, or designing deduplication that distinguishes records without replaying them. Simply changing `>` to `>=` would repeat events on every poll.

## Midnight and offline periods

Each poll requests only the current day in Home Assistant's time zone. If a poll occurs at 23:59:50 and an access occurs at 23:59:55, the next poll at 00:00:10 requests the new day and may miss that access permanently.

A recovery window covering previous records and offline periods, combined with correct deduplication, is still needed. Accounts with homes in different time zones from HA also require additional date and time verification.

## Unexpected Yale responses

Some HTTP statuses and top-level response types are checked, but parsing assumes parts of the internal account, device, and access-record structures. Missing or unexpected values can cause exceptions and affect updates. Although history is intended to be optional, malformed records can still fail an entire update.

Anonymized response samples and boundary validation are needed, including isolation of invalid records without inventing a lock state.

## Other restrictions

- State depends on the internet connection, hub, and unofficial Yale API. It may be delayed, unknown, or unavailable.
- HTTP 429 and 5xx are treated as temporary failures, but `Retry-After` does not yet receive special handling to adjust polling.
- The first history read during startup or reload is used as a baseline and is not emitted as new activity. Events occurring during startup may be part of that baseline and never be emitted.
- The last unlock is kept in memory and rebuilt only from the requested day. After a restart, it may remain unknown until the next unlock.
- All locks in an account share its configured PIN. There is no per-device PIN or device selection setting.
- Newly added devices require an integration reload. Firmware and other device metadata are not dynamically refreshed in all cases.
- Setup forms have English and Spanish translations; entity names remain fixed in English.
- Real-world validation currently covers one Yale YDM 60 with a Yale Connect account in Peru, not a model or region compatibility matrix.

## Fixes already included

- HTTP 429 and 5xx are not mistaken for invalid credentials.
- The PIN uses a password selector in setup and options forms.
- Command errors do not include the server response body.
- Removing a lock cancels its pending operation without raising a `KeyError`.

Regression tests cover those four fixes. They do not demonstrate that the limitations above have been resolved.
