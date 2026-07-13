# 4 — No xdist While Worker Startup Dominates

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-13

## Context

- pytest core has no parallel execution; parallelism requires the `pytest-xdist` plugin
- measured on this suite (61 tests): serial 0.30s, `--numprocesses=4` 0.52s,
  `--numprocesses=2` 0.57s — the ~0.25s worker spin-up floor exceeds the entire serial
  runtime, so every parallel configuration is slower than the single run

## Decision

- `pytest-xdist` stays out of the dependencies; `mise run test` runs plain `uv run pytest`
- reintroduce xdist only once a measured parallel run beats the serial run on this suite —
  the measurement, not suite size or test count, is the criterion

## Consequences

- re-evaluation is cheap: `uv add --group dev pytest-xdist`, run
  `uv run pytest --numprocesses=4`, compare against serial, keep whichever wins
- integration tests that spawn subprocesses (the generated-docs pair) grow the serial
  runtime fastest and are the likeliest trigger for the re-measurement
