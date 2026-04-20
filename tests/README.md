# Tests

## Snapshot baselines

PNG baselines for each EPL2 fixture live under `tests/epl2/test_snapshots/`,
keyed by fixture stem (for example, `epl1-55x34.png`). They are byte-exact
golden files.

### Regenerate after intentional renderer changes

1. Run `pytest tests/epl2/test_snapshots.py --force-regen` to rewrite the
   baselines from the current renderer output.
2. Open each regenerated PNG and human-review it against the matching
   printed photo in `examples/epl*.jpeg`.
3. Commit the updated baselines in a single, reviewable commit.

Never commit `--force-regen` output without the human review step.
