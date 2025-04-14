## TTL, Start_at & End_at

Among these three time units, you must enter one related to the end (end_at). Or you can set `persist = true` to ignore
the expiration time.
When you set `start_at`, the room card will be allowed to be verified after the arrival time. If you do not set this, it
is the start time when the API request reaches the server.

For input or not, we have derived 8 cases to help you decide how to use this feature.

| Case | `ttl` Provided | `start_at` Provided | `end_at` Provided | Behavior                                                                                  |
|------|----------------|---------------------|-------------------|-------------------------------------------------------------------------------------------|
| ①    | ✅ Yes          | ❌ No                | ❌ No              | `start_at = now`; `end_at = start_at + ttl`; Redis TTL is set.                            |
| ②    | ✅ Yes          | ✅ Yes               | ❌ No              | Uses given `start_at`; `end_at = start_at + ttl`; Redis TTL is set.                       |
| ③    | ✅ Yes          | ❌ No                | ✅ Yes             | Ignores `end_at`; `start_at = now`; `end_at = start_at + ttl`; Redis TTL is set.          |
| ④    | ✅ Yes          | ✅ Yes               | ✅ Yes             | Ignores `end_at`; `end_at = start_at + ttl`; Redis TTL is set.                            |
| ⑤    | ❌ No           | ✅ Yes               | ✅ Yes             | `ttl = end_at - now`; `start_at` is respected; Redis TTL is set.                          |
| ⑥    | ❌ No           | ✅ Yes               | ❌ No              | [Error] When ttl is not set and persist is False, end_at must be provided.                |
| ⑦    | ❌ No           | ❌ No                | ✅ Yes             | `start_at = now`; `ttl = end_at - now`; Redis TTL is set.                                 |
| ⑧    | ❌ No           | ❌ No                | ❌ No              | [Error] At this time, you must set `persist = true`, otherwise an error will be reported. |

### Special Rule: `persist = true`

If `persist = true`, TTL will always be set to `None` regardless of `ttl` or `end_at`.  
The card will **not expire in Redis**, and must be managed manually. `start_at` is still respected for activation
control.

## owner_client_id field

This is used to identify who posted the card.

Does not affect the verification process of unlocking. But it is useful when querying the registered card number.
