# Migration Notes

## Chronicle inline snapshot compatibility

Chronicle history snapshots saved before the inline refactor stored the inline
context under the `inline_id` key. Loading those snapshots now raises a
`ValueError` so that the legacy data is not silently ignored. If you still have
FSM storage entries created before this change, clear or resave them so that the
inline value is persisted under the new `inline` slot before starting the
application.

## Chronicle extras integer validation

Chronicle message payloads now require that every entry in the `extras` list is
already persisted as an integer. Older snapshots may still contain those values
as strings (for example `"123"`). Before rolling out this version, migrate the
stored FSM history by rewriting each entry to use integers instead of strings.
One approach is to load the stored JSON, replace `message["extras"] = [int(v)
for v in message["extras"]]`, and save the updated payload back to your FSM
storage.
