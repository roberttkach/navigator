# Renaming Plan

## Objectives
- Ensure every identifier uses a single, meaningful word.
- Avoid underscores outside of leading underscores and existing constants.
- Prefer short, precise terms that preserve intent.

## Completed Adjustments
- Telegram router handlers now expose the callback handler as `retreat` and the text handler as `recall`, with `_tongue` providing locale detection.
- Telegram scope builder renamed to `outline`, imported through the composition root as `forge`.
- Navigator tail helper now relies on `_tailer` and uses `identifier`/`status` for clarity when referencing message identifiers and state values.
- Domain storage contracts now use single-word verbs: history repositories `recall`/`archive`, state repositories `status`/`assign`/`payload`, last message repositories `peek`/`mark`, and temporary repositories `collect`/`stash`.
- Application service decorator `log_io` shortened to `trace`, with `augment` replacing the `extra_fn` callback for additional log context.
- Telegram serialization helpers now expose `decode`/`preview`/`caption`/`restate`, with `cleanse`/`divide`/`scrub` guarded by extra `audit`/`screen` checks.
- Telegram media helpers adopt `weblink`/`adapt`/`convert`/`compose`/`assemble`, with inline strategy injection renamed to `probe`/`strictpath` and Settings following suit.
- Message gateway protocol promotes edit verbs to `rewrite`/`recast`/`retitle`/`remap`, with orchestrator dispatch updated to the new names.
- Telegram gateway internals now use single-word identifiers throughout dispatch/edit/delete flows, including the extras bundle handling, `DeleteBatch` runner, and the shared `targets`/`extract` helpers with `sanitize` alignment.
- Inline editing helpers remove the `handle_element`/`_media_editable_inline`/`_reply_changed` names in favour of `handle`, `_inlineable`, and `_replydelta`, dropping the auxiliary `_inline_remap` alias for a streamlined `_inline` import.
- Rebase flow shifter dependencies shorten to `ledger`/`buffer`/`latest`, with the pivot message handled through `marker`/`patched`/`trailer`/`rebuilt` terminology.
- Tail use-case adopts `latest`/`ledger` storage naming, exposes the public `peek` verb, and keeps inline decisions readable through `normal`/`choice`/`mapped`/`targets`/`resend` markers.
- Logging decorator utilities now rely on `_capture` and `_snapshot`, with the `trace` decorator exposing the public `begin`/`success`/`skip` argument trio for clarity.
- Gateway error pattern builders collapse to the classmethod `collect`, removing the final `from_phrases` snake-case entry point.
- Gateway result metadata now settles on single-word keys `medium`/`file`/`clusters`, with the view orchestrator mirroring the terminology through its `rendering` profile accessor.
- View orchestrator API now exposes `render` with single-word helpers (`head`/`album`/`refine`/`verify`) and accumulators (`primary`/`bundles`/`notes`) to replace the legacy `render_node` flow.
- Storage adapters drop the `Repo` abbreviation by renaming the persistent stores to `Chronicle`/`Latest`/`Status`/`Buffer` modules and aligning the dependency container with the new single-word classes.
- Domain history message entity now uses the full word `Message`, with mapper/store helpers replacing `msg`/`msgs` locals by `message`/`messages` and removing short aliases such as `mid`/`idx`/`vk`.
- Last message storage protocol shortened to `LatestRepository`, with adapters and use-cases updated accordingly.
- Telegram helpers adopt single-word module names (`screen`, `codec`) while the state tracker is consolidated under the `status` module for clarity.
- FSM state payload helper now maps data through `mapping`, replacing the interim `data_map` alias.
- Telegram gateway helpers drop the `media_mapper` alias in favour of direct `media.compose`/`assemble`/`convert`/`adapt` usage.
- Serializer and logging utilities now reference standard helpers through their parent modules (`dataclasses.is_dataclass`, `time.perf_counter`), and protocol decorators rely on `typing.runtime_checkable` to keep local namespaces underscore-free.
- Navigator logging context uses the single-word `handlers` key when capturing callback metadata.
- View orchestrator internals drop single-letter placeholders by funnelling decision flow through `verdict`, mapping gateway outputs to `result`, and aligning album iteration on `stored`/`incoming` counters and `latest` media markers.
- Storage helpers replace residual one-letter locals: persistence now accepts an `operation` keyword, the history chronicle iterates over each `record`/`message`, status payload filters operate on `key`/`value` pairs, and the view ledger exposes the collected `signature`.

## Next Steps
- Migrate remaining domain and application layer helpers (e.g., mapper converters, orchestrator builders) that still rely on snake_case naming to single-word equivalents while keeping semantic clarity.
- Replace abbreviations such as `uc`, `msg`, `cfg`, and similar throughout the repository with full words.
- Audit adapter-layer gateway helpers (e.g., `do_edit_text`, `reply_for_send`) and select concise replacements that respect the single-word rule.
- Extend presenter-facing protocols (e.g., `send_media`) to the new single-word vocabulary established for the gateway.
- Continue migrating dependency-injection providers and application use-case locals (e.g., `history_repo`, `to_delete`) away from snake_case once core gateway flows stabilise.
- Align tail orchestration helpers with the inline vocabulary by renaming locals such as `base_msg`/`ids_to_del`/`last_entry` to concise single-word alternatives after the new inline strategy API settles.

## Gateway Renaming Plan

| Scope | Legacy Identifier | Replacement |
|-------|-------------------|-------------|
| Telegram gateway helpers | `do_send` | `dispatch` |
| Telegram gateway helpers | `do_edit_text` | `rewrite` |
| Telegram gateway helpers | `do_edit_media` | `recast` |
| Telegram gateway helpers | `do_edit_caption` | `retitle` |
| Telegram gateway helpers | `do_edit_markup` | `remap` |
| Telegram reply helpers | `reply_for_send`/`reply_for_edit` | `markup(codec, reply, *, edit)` |
| Gateway logging helpers | Inline replacements for `log_edit_fail`/`log_edit_ok` | Inline `jlog` calls |
| Telegram batch delete runner | `BatchDeleteRunner` | `DeleteBatch` |

## Tail Use-Case Renaming Plan

| Scope | Legacy Identifier | Replacement |
|-------|-------------------|-------------|
| Last message flow | `last_repo` | `latest` |
| Last message flow | `_last_repo` | `_latest` |
| Last message flow | `history_repo` | `ledger` |
| Last message flow | `_history_repo` | `_ledger` |
| Last message flow | `get_id` | `peek` |
| Last message flow | `new_history` | `trimmed` |
| Last message flow | `new_last_id` | `marker` |
| Last message flow | `last_node` | `tail` |
| Last message flow | `last_entry` | `anchor` |
| Last message flow | `base_msg` | `stem` |
| Last message flow | `ids_to_del` | `targets` |
| Last message flow | `resend_result` | `resend` |

## Rebase Use-Case Renaming Plan

| Scope | Legacy Identifier | Replacement |
|-------|-------------------|-------------|
| Rebase flow | `history_repo` | `ledger` |
| Rebase flow | `_history_repo` | `_ledger` |
| Rebase flow | `temp_repo` | `buffer` |
| Rebase flow | `_temp_repo` | `_buffer` |
| Rebase flow | `last_repo` | `latest` |
| Rebase flow | `_last_repo` | `_latest` |
| Rebase flow | `new_id` | `marker` |
| Rebase flow | `patched_first` | `patched` |
| Rebase flow | `rebased_last` | `trailer` |
| Rebase flow | `rebased` | `rebuilt` |

## Upcoming Protocol Updates

- Promote `MessageGateway` verbs such as `edit_text`, `edit_media`, `edit_caption`, and `edit_markup` to single-word alternatives once downstream call sites have adopted the helper renames listed above.
- Audit downstream consumers for the new `medium`/`file`/`clusters` metadata vocabulary to ensure compatibility across storage and presentation layers.

## Storage Adapter Renaming Plan

| Scope | Legacy Identifier | Replacement |
|-------|-------------------|-------------|
| FSM storage modules | `adapters.storage.historyrepo` | `adapters.storage.chronicle` |
| FSM storage modules | `HistoryRepo` | `Chronicle` |
| FSM storage modules | `adapters.storage.lastrepo` | `adapters.storage.latest` |
| FSM storage modules | `LastRepo` | `Latest` |
| FSM storage modules | `adapters.storage.staterepo` | `adapters.storage.status` |
| FSM storage modules | `StateRepo` | `Status` |
| FSM storage modules | `adapters.storage.temprepo` | `adapters.storage.buffer` |
| FSM storage modules | `TempRepo` | `Buffer` |
| Last repository API | `mark(id)` parameter name | `mark(marker)` |

Renaming these adapters removes the lingering abbreviation-based names, keeps file names to a single descriptive word, and makes the dependency-injection providers read naturally (`chronicle`, `status`, `latest`, `buffer`).

## View Restoration Plan

| Scope | Legacy Identifier | Replacement |
|-------|-------------------|-------------|
| View restorer service | `restore_node` | `revive` |
| View restorer service | `_try_dynamic_restore` | `_dynamic` |
| View restorer service | `_static_restore_msg` | `_static` |
| View restorer logging | `factory_key` keyword | `forge` |

## Guidelines for Future Renames
- When multiple contexts share similar operations, choose consistent vocabulary (e.g., prefer `store`/`load` across repositories).
- Use existing domain terminology (history, tail, scope, ledger) to inform replacement words instead of inventing artificial compounds.
- Validate each rename with type checkers or runtime smoke tests to avoid behavioural regressions.
