# Migration Notes

## Chronicle inline snapshot compatibility

Chronicle history snapshots saved before the inline refactor stored the inline
context under the `inline_id` key. Loading those snapshots now raises a
`ValueError` so that the legacy data is not silently ignored. If you still have
FSM storage entries created before this change, clear or resave them so that the
inline value is persisted under the new `inline` slot before starting the
application.
