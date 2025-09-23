# Migration Notes

## Chronicle extras integer validation

Chronicle message payloads now require that every entry in the `extras` list is
already persisted as an integer. Older snapshots may still contain those values
as strings (for example `"123"`). Before rolling out this version, migrate the
stored FSM history by rewriting each entry to use integers instead of strings.
One approach is to load the stored JSON, replace `message["extras"] = [int(v)
for v in message["extras"]]`, and save the updated payload back to your FSM
storage.
