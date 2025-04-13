## TTL, Start_at & End_at

Rule:

1. TTL Priority Principle:
   If `ttl` is set, Redis expiration control is performed using `ttl` as the only basis.

- `start_at` will automatically set as the current time (that is, the start time) when the server receives the API
  request.
- `end_at` will be automatically derived based on `start_at + ttl` (if not specified explicitly).

2. When `ttl` is null (or not provided):
   The `start_at` and `end_at` will be used to control the valid time on the card logic (application layer control
   enablement and query).

- Redis will not set the expiration time, the card data will continue to exist, and the validity needs to be managed by
  the application logic.
- The application needs to confirm `now >= start_at` and `now <= end_at` to use the card.

3. Special circumstances:
   If `end_at` is provided but `ttl` is not provided, the system will automatically calculate `ttl = end_at - now`,
   and use it for Redis's TTL control (if the result is > 0, set the expiration time).

4. When `persist = true`:
   It means that the card is a permanent valid card. The system will not set TTL, and the data in Redis will not expire
   automatically.
   The administrator needs to manually remove or rely on the application layer logic to determine whether it is
   available.

Note:

- All expiration controls are controlled by Redis TTL and do not depend on `end_at`.
- The application layer only needs to determine whether the card is enabled (i.e. `now >= start_at`).

Logic:

```
IF persist == True:
    TTL = None
ELSE IF ttl is provided:
    use ttl
    start_at = now (or from user)
    end_at = start_at + ttl
ELSE IF end_at is provided:
    start_at = now (or from user)
    ttl = end_at - now
ELSE:
    start_at = now
    ttl = None
```

### Card Expiration Behavior (`ttl`, `start_at`, `end_at`)

| Case | `ttl` Provided | `start_at` Provided | `end_at` Provided | Behavior                                                                                  |
|------|----------------|---------------------|-------------------|-------------------------------------------------------------------------------------------|
| ①    | ✅ Yes          | ❌ No                | ❌ No              | `start_at = now`; `end_at = start_at + ttl`; Redis TTL is set.                            |
| ②    | ✅ Yes          | ✅ Yes               | ❌ No              | Uses given `start_at`; `end_at = start_at + ttl`; Redis TTL is set.                       |
| ③    | ✅ Yes          | ❌ No                | ✅ Yes             | Ignores `end_at`; `start_at = now`; `end_at = start_at + ttl`; Redis TTL is set.          |
| ④    | ✅ Yes          | ✅ Yes               | ✅ Yes             | Ignores `end_at`; `end_at = start_at + ttl`; Redis TTL is set.                            |
| ⑤    | ❌ No           | ✅ Yes               | ✅ Yes             | `ttl = end_at - now`; `start_at` is respected; Redis TTL is set.                          |
| ⑥    | ❌ No           | ✅ Yes               | ❌ No              | Only `start_at` is used for activation; no Redis TTL; card does not expire automatically. |
| ⑦    | ❌ No           | ❌ No                | ✅ Yes             | `start_at = now`; `ttl = end_at - now`; Redis TTL is set.                                 |
| ⑧    | ❌ No           | ❌ No                | ❌ No              | `start_at = now`; no TTL; card never expires; manual control only.                        |

---

### Special Rule: `persist = true`

If `persist = true`, TTL will always be set to `None` regardless of `ttl` or `end_at`.  
The card will **not expire in Redis**, and must be managed manually. `start_at` is still respected for activation
control.

## owner_client_id field

This is used to identify who posted the card.

Does not affect the verification process of unlocking. But it is useful when querying the registered card number.

()[]