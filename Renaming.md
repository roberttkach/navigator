# Renaming Strategy

## Objectives
- Converge every identifier on a single clear word (classes may use two) without internal underscores.
- Keep the code semantics intact by selecting concise synonyms that still convey intent.
- Tackle the refactor in batches ordered by dependency depth to reduce churn.

## Completed Adjustments
- `sitecustomize.py`: renamed the package pointer variable to `_package` to eliminate the internal underscore.
- `infrastructure.config.Settings`: renamed fields to one-word synonyms (`retention`, `thumbguard`, `redaction`) and updated the container, rendering config, and composition bootstrap to use them.
- Rendering configuration objects now expose the boolean guard as `thumbguard` so downstream checks use a compliant identifier.

## Upcoming Phases
1. **Infrastructure layer sweep**
   - Rename locking utilities: e.g., `_LatchLike` methods such as `acquire`, `release`, `untether` stay, but helpers like `_key`, `_current`, `_LatchAdapter` need concise words (`_pivot`, `_active`, `_Latch`, etc.).
   - Revisit dependency injection providers so every exposed factory/property (`history_repo`, `state_repo`, `temp_repo`) becomes a one-word noun (`archive`, `registry`, `stash`).
2. **Application services**
   - Replace underscored helpers in view orchestration (`_media_editable_inline`, `_reply_changed`) with short verbs (`_allowedit`, `_replydiff`).
   - Align use case dependencies (`history_repo`, `last_repo`, `state_repo`) with the provider renames from phase 1.
   - Simplify logging hooks (`log_io`) and payload mappers (`collect`, `convert`) to single-word verbs where necessary.
3. **Adapters**
   - Telegram gateway modules contain snake_case helpers (`retry_request`, `make_payload`); map each to crisp verbs (`retry`, `compose`).
   - Storage adapters use `*_repo`/`*_keys` suffixes; collapse to standalone nouns (`ledger`, `vault`, `cursor`).
4. **Domain model**
   - Error hierarchy currently uses multiword class names (`MessageEditForbidden`); shorten to one- or two-word nouns (`EditBan`, `EditVoid`).
   - Value objects expose attributes like `message_effect_id`; introduce alias layers so external API keys remain untouched while internal attributes become compliant (`effect`, `effectid` wrapper properties).
   - Rendering helpers (`_text_extra_equal`, `_has_any_media`) should be renamed to minimal verbs (`_textequal`, `_hasmedia`).
5. **Presentation layer and tests**
   - Navigator API uses methods such as `get_id`; switch to `getid` via wrapper objects or redesign call sites to respect rule 3 by choosing substitute verbs (`fetch`, `mark`).
   - Update test modules currently named `test_retry.py` to a one-word form like `retrycase.py` while keeping pytest discovery (`test` prefix) via module-level `pytestmark`.

## Execution Notes
- Progress through the dependency graph from lowest-level utilities upward, renaming call sites after each layer to maintain runnable builds.
- Provide compatibility shims (temporary properties or wrappers) during transition phases when external APIs demand snake_case names.
- After each batch, run the full test suite (`pytest`) and static analyzers (`ruff`, `mypy`) to ensure behavior parity.
- Update documentation and developer guides to explain the new vocabulary once the renaming is complete.
