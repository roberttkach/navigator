# Renaming Plan

This repository currently mixes descriptive snake_case names with the new
single-word naming policy. The plan below documents the migration strategy and
captures the renames performed in this iteration together with the remaining
work.

## Rules Recap

* Prefer a single clear word for all public identifiers. Classes may use up to
  two capitalised words (PascalCase).
* Underscores are only permitted as a leading prefix (for private helpers) or
  inside upper-case constants.
* Do not create glued variants of the previous snake_case names. Instead pick a
  concise single word that conveys the same idea.
* Apply the policy uniformly to modules, functions, methods, attributes and
  variables as they become part of the public surface.

## File Name Plan

The same rules now govern the file system layout. Packages keep their mandatory
`__init__.py` markers, but every other module should be a single clear word.
Auxiliary tooling such as IDE metadata is removed when it cannot follow the
convention.

### Completed

| Old path | New path | Notes |
| -------- | -------- | ----- |
| `adapters/telemetry/python_logging.py` | `adapters/telemetry/logger.py` | Describes the telemetry adapter without underscores. |
| `.idea/` (directory) | Removed | JetBrains metadata dropped so that no tracked file name violates the policy. |

### Remaining

* Audit future contributions to ensure new modules join the one-word scheme.
* When configuration assets are necessary, prefer directory names that already
  satisfy the rule so that internal files inherit compliant names.

## Completed Renames

| Scope | Old name | New name | Notes |
| ----- | -------- | -------- | ----- |
| Public API | `api.build_navigator` | `api.assemble` | Propagated through bootstrap modules and entry points. |
| Presentation | `presentation.alerts.prev_not_found` | `presentation.alerts.missing` | Keeps the absent-history alert. |
| Presentation | `presentation.alerts.inline_unsupported` | `presentation.alerts.barred` | Signals that inline mode is not supported. |
| Presentation | `presentation.alerts.back_label` | `presentation.alerts.revert` | Supplies the “Back” button label. |
| Presentation | `presentation.telegram.router.configure_telemetry` | `presentation.telegram.router.instrument` | Describes telemetry wiring with a single word. |
| Tests | `trial.stub_telemetry` | `trial.monitor` | Returns a monitoring stub for telemetry. |
| Tests | `trial.noop_guard` | `trial.sentinel` | Async context manager used as guard stub. |
| Tests | `trial.digest_*` helpers | `reliance`, `override`, `absence`, `veto`, `assent`, `surface`, `rebuff`, `refuse`, `decline`, `siren`, `wording`, `translation`, `commerce`, `fragments` | Bring the scenario helpers in line with the policy. |
| Core limits | `Limits.text_max`, `caption_max`, `album_floor`, `album_ceiling`, `album_blend` | `textlimit`, `captionlimit`, `groupmin`, `groupmax`, `groupmix` | Protocol names and all adapters now share the single-word vocabulary. |
| Core limits | `ConfigLimits` constructor `floor`, `ceiling`, `blend` | `minimum`, `maximum`, `mix` | Keeps the configuration wiring aligned with the new protocol. |
| Settings | `text_limit`, `caption_limit`, `album_floor`, `album_ceiling`, `album_blend`, `album_blend_set`, `delete_delay`, `delete_delay_ms` | `textlimit`, `captionlimit`, `groupmin`, `groupmax`, `mixcodes`, `mixset`, `deletepause`, `deletepausems` | Updated environment mapping and dependency injection bindings. |
| Telegram gateway | `delete_delay` argument | `deletepause` | Matches the configuration name and emphasises the pacing behaviour. |
| Extra schema | `ExtraSchema.for_send`, `for_edit`, `for_history` | `send`, `edit`, `history` | Reflected in the Telegram serializer and gateway usage. |
| Gateway util | `result_from_message` | `derive` | Shortens the helper that builds message results. |
| Presentation | `presentation.markup.sanitize_caption` | `presentation.markup.purify` | Keeps the markup helper compliant even though it is currently unused. |
| View planner | `_RenderState.add_existing`, `_RenderState.add_execution` | `retain`, `collect` | Reduces the remaining snake_case verbs inside the planner flow. |
| Settings | `infra.config.settings.history_limit` | `historylimit` | Settings field and dependency overrides now share the one-word form. |
| Inline policy | `app.internal.policy.validate_inline` | `app.internal.policy.shield` | Collapses the inline payload guard into a single verb. |
| View executor | `app.service.view.executor.refine_meta` | `app.service.view.executor.refine` | Shortens the metadata adjustment hook and updates planner call sites. |
| Album service | `AlbumService.partial_update` | `AlbumService.refresh` | Adopts a concise verb for partial album rewrites. |
| Album service | `_album_ids`, `_alter`, `_clone`, `_clusters` | `_lineup`, `_changed`, `_copy`, `_collect` | Private helpers now use one-word suffixes. |
| Inline handler | `_handle_media`, `_handle_text`, `_fallback_markup` | `_mediate`, `_scribe`, `_fallback` | Inline helpers follow the single-word suffix rule. |
| Tests | `trial.refine_meta` stub, `partial_update` stubs | `trial.refine` stub, `refresh` stubs | Synchronises test doubles with the runtime names. |
| Bootstrap | `bootstrap.navigator._convert_scope` | `bootstrap.navigator._scope` | Scope adapter inlines the single-word helper. |
| Tail workflow | `Tailer._render_result`, `Tailer._apply_inline` | `Tailer._result`, `Tailer._inlay` | Streamlines the edit pipeline internals. |
| Setter workflow | `Setter._load_history`, `_revive_payloads`, `_apply_render`, `_patch_entry` | `Setter._history`, `_revive`, `_imprint`, `_patch` | Aligns the state restoration helpers with the policy. |
| Preview codec | `TelegramLinkPreviewCodec._optional_flag` | `TelegramLinkPreviewCodec._maybe` | Shortens the optional flag decoder. |
| Media adapter | `adapters.telegram.media._media_handler` | `adapters.telegram.media._creator` | Picks media constructors with a single noun. |
| Settings | `infra.config.settings._environment_overrides` | `infra.config.settings._environ` | Keeps configuration loading compliant with the naming scheme. |
| Inline guard | `app.service.view.inline.guard._primary_media` | `app.service.view.inline.guard._primary` | Refines the media probe helper. |
| View planner | `_apply_album_head`, `_sync_slots`, `_apply_inline`, `_record_inline`, `_apply_regular`, `_trim_tail`, `_append_missing` | `_header`, `_align`, `_inset`, `_record`, `_regular`, `_prune`, `_append` | Brings the planning workflow verbs down to single words. |

## Scheduled Renames

The remaining snake_case identifiers are grouped by module so that each block can
be addressed incrementally. Proposed target names are provided for future work:

* Identify any remaining compound identifiers in the inline workflow once new
  features land and continue migrating them to the single-word style.

Each future step should follow the same approach as this update: choose the
shortest precise word, refactor call sites, and update exports (`__all__`,
re-export modules, and docstrings).
