# Security review (author's review, not an independent audit)

Scope: `server/app.py`. The server accepts a nickname and 12 numbers, nothing else. It never executes, parses as code or stores anything else from a client, and keeps no personal data (IP addresses live in memory only, for rate limiting).

Handled, with tests in `tests/test_arena.py`: range and length validation, NaN, wrong types, nickname character set and length, duplicate nicknames (409), rate limit of 10 submissions per minute per IP (429), entry cap of 200 (503), admin delete only with `ADMIN_TOKEN` (disabled when unset), CORS only for `ALLOWED_ORIGINS`, validation errors never echo submitted values.

Found during review and fixed: (1) a NaN submission crashed the error response with a 500; (2) scoring is O(n^2), so an unbounded leaderboard was a CPU denial-of-service risk; now capped at 200 entries and cached until entries change (200 x 200 pairs measured at 0.74 s on the author's sandbox).

Known limits: no accounts, so anyone can fill the cap or submit offensive nicknames (delete with the admin route); the rate limiter is per process and resets on restart; behind a proxy it needs `--proxy-headers` and a correct `FORWARDED_ALLOW_IPS`; one SQLite file means one instance; TLS is the host's job; no load testing has been done.
