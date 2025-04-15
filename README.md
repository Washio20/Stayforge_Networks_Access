Document:
https://identify.access.networks.stayforge.io/docs/

Login the Stayforge ID here:

[/login](/login) | [/logout](/logout)

---

**Stayforge Networks Access (SNA)** is a centralized identity and device access control service designed for modern IoT
and
enterprise environments. It supports verification based on card numbers, barcodes, and QR codes, and integrates
seamlessly with a variety of terminal devices such as QR readers and smart door controllers through secure and efficient
APIs.

With SNA, organizations can:

- Securely register and manage visitor or guest cards
- Bind cards to specific devices (identified by Device SN or MAC address)
- Configure activation timeframes, TTLs, and persistence flags
- Instantly verify whether a card is valid and determine access permission
- Authenticate API calls using OAuth 2.0 and JWT tokens

Whether it’s hotel room locks, office entry points, or temporary access scenarios, SNA ensures every access decision is
fast, secure, and auditable.


---

## Stayforge Networks Access Verification Flow

Terminal devices from Stayforge Networks (e.g., QR Readers) use their **MAC address**, **Serial Number (SN)**,
or **Device ID** as credentials to send scanned **card numbers** or **barcode/QR code content** to the **SNA
verification
server**.  
The SNA server checks whether the submitted card number exists in its database and responds with a command indicating
whether to unlock the door.

### Verification Process

1. The terminal device sends the following information to the SNA server:
    - Device Serial Number (SN) or Device ID
    - Scanned card number / barcode / QR code

2. The SNA verification server checks if the card exists in the database.

3. Based on the verification result, the server responds with:
    - Command to unlock
    - Command to deny access

> The terminal device only transmits data and executes the server's command — it does not perform any local
> verification.

### Card Registration Process

To register a new card in the system:

1. The user must first sign in via **Stayforge ID** for authentication.
2. After signing in, obtain an `access_token`.
3. Use the `access_token` to call the SNA API and register the card.

> Only cards that exist in the SNA database will be permitted to unlock doors.

---

## Quickstart

Usually, adding, deleting and modifying card information requires identity authentication. However, the terminal control
endpoint does not require authentication.

To simply, If you want to add a new card to the system, you need to log in to the Stayforge ID as verification and then
pass in access_token when calling the API.

### Step.1 Login to Stayforge

Login Stayforge ID and get access token here -> [/login](/login)

### Step.2 Note down the tokens

After logging in, you will get a json data, which looks like this:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "id_token": "...",
  "scope": "openid profile email offline_access",
  "expires_in": 86400,
  "token_type": "Bearer"
}
```

`access_token` and `refresh_token` will be automatically recorded in Httponly cookies for your future testing (But you
are still advised to write them down manually).

### Step.3 Try NSA API

Here are some examples:

```shell
# Add a new card to SNA
curl -X POST https://identify.access.networks.stayforge.io/card/add \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Environment: standard" \
  -d '{
    "number": "6B06C2A25E99C68EDCBE",
    "name": "Guest Card",
    "devices": [
      "hotel-door-101",
      "hotel-door-102"
    ],
    "start_at": "2025-04-13T00:00:00Z",
    "end_at": "2025-04-20T00:00:00Z",
    "created_at": "2025-04-13T04:50:00Z",
    "owner_client_id": "client_etoehotel"
  }'
# Identify a card
```

### Step.4 Refresh Token via Auth0

To refresh access tokens, clients should directly request new tokens from Auth0 using the standard OAuth 2.0
refresh_token grant. For security and isolation purposes, Stayforge Networks Access does not proxy this operation.

```shell
curl -X POST https://auth.stayforge.io/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "refresh_token",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## About DateTime Format and Timezone Handling

All datetime fields in the API (e.g. `start_at`, `end_at`, `created_at`) **must follow ISO 8601 format** and are
expected to be in **UTC by default** unless otherwise specified.

#### Default Behavior

- If you omit the timezone, the system will assume the datetime is in **UTC (Coordinated Universal Time)**.
- Example (UTC time):

  2025-04-12T08:00:00Z

#### Timezone-Aware Datetime

If your system or users operate in **non-UTC timezones** (e.g. Japan Standard Time, UTC+9), you **must provide timezone
information explicitly** to avoid misunderstanding.

- Example (Japan time):

  2025-04-12T17:00:00+09:00

> If you provide a datetime without timezone info (e.g. `2025-04-12T17:00:00`), the server will treat it as **UTC**,
> which may lead to incorrect activation or expiration timing.

#### Summary

- Always use full ISO 8601 format with timezone offset.
- Default to UTC if no timezone is provided.
- Specify timezone if your clients are in a local time zone (e.g. `+09:00` for JST).
