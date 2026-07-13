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

## Break-even model

Parallel wall time fits `parallel ≈ floor + serial / n`, where `floor` is the per-machine
worker-startup cost — derive it from one throwaway parallel run as `parallel − serial / n`
(the 2026-07 datapoints in Context both yield the same floor on the machine that recorded
them, confirming the model). Parallel wins once

```text
serial > floor × n / (n − 1)
```

so 2 workers need the serial run to exceed twice the floor, 4 workers 4/3 of it. Absolute
seconds are deliberately not part of the criterion — floors differ per CPU; measure yours.
Rule of thumb: once the serial suite exceeds roughly double your measured floor, run the
comparison.

## Consequences

- re-evaluation is cheap: `uv add --group dev pytest-xdist`, run
  `uv run pytest --numprocesses=4`, compare against serial, keep whichever wins
- integration tests that spawn subprocesses (the generated-docs pair) grow the serial
  runtime fastest and are the likeliest trigger for the re-measurement
