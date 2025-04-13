Document:
https://identify.access.networks.stayforge.io/docs/


## About DateTime Format and Timezone Handling

All datetime fields in the API (e.g. `start_at`, `end_at`, `created_at`) **must follow ISO 8601 format** and are expected to be in **UTC by default** unless otherwise specified.

#### Default Behavior
- If you omit the timezone, the system will assume the datetime is in **UTC (Coordinated Universal Time)**.
- Example (UTC time):

   2025-04-12T08:00:00Z

#### Timezone-Aware Datetimes
If your system or users operate in **non-UTC timezones** (e.g. Japan Standard Time, UTC+9), you **must provide timezone information explicitly** to avoid misunderstanding.

- Example (Japan time):

   2025-04-12T17:00:00+09:00

> If you provide a datetime without timezone info (e.g. `2025-04-12T17:00:00`), the server will treat it as **UTC**, which may lead to incorrect activation or expiration timing.

#### Summary
- Always use full ISO 8601 format with timezone offset.
- Default to UTC if no timezone is provided.
- Specify timezone if your clients are in a local time zone (e.g. `+09:00` for JST).
