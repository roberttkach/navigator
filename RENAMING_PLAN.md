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

## Scheduled Renames

The remaining snake_case identifiers are grouped by module so that each block can
be addressed incrementally. Proposed target names are provided for future work:

* `core.port.limits.Limits`: rename `text_max`, `caption_max`, `album_floor`,
  `album_ceiling`, `album_blend` to single-word counterparts such as
  `textcap`, `captioncap`, `albumfloor`, `albumceiling`, `albumblend`, and
  update all adapters implementing the protocol.
* `core.port.extraschema.ExtraSchema`: rename `for_send`, `for_edit`,
  `for_history` to concise verbs like `send`, `edit`, and `history`, mirrored in
  the Telegram serializer implementations.
* `presentation.markup.sanitize_caption`: shorten to a single action word such
  as `sanitize` and adjust importers.
* `adapters.telegram.gateway.util.result_from_message`: compress into an
  accurate single word (e.g. `extract`) used consistently by the gateway.
* `app.service.view.planner` and related inline/album helpers: rename the public
  methods that still rely on snake_case (e.g. `add_existing`, `add_execution`)
  using domain-specific verbs (`attach`, `enqueue`, etc.).
* `infra.config.settings.album_blend_set` and `delete_delay`: rename to
  `albumblend` and `deletemoment` or other precise words.

Each future step should follow the same approach as this update: choose the
shortest precise word, refactor call sites, and update exports (`__all__`,
re-export modules, and docstrings).
