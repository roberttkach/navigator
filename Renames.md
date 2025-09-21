# Renaming Plan

## Completed updates

The rendering album module has been switched to single-word identifiers:

| Previous name | New name | Notes |
| --- | --- | --- |
| `validate_group` | `validate` | Entry point for album validation. |
| `album_kind` | `nature` | Returns album media classification. |
| `album_compatible` | `aligned` | Checks whether two albums can be edited in place. |
| `_group_invalid_reasons` | `_audit` | Collects validation issues for albums. |
| `invalid_size` | `limit` | Exception flag tracking size violations. |
| `forbidden_types` | `forbidden` | Exception flag for disallowed media kinds. |
| `audio_mixed` | `audio` | Exception flag for mixed audio albums. |
| `document_mixed` | `document` | Exception flag for mixed document albums. |
| `soft_ignorable` | `dismissible` | Telegram error text filter renamed to a single word. |
| `_iter_exc_chain` | `_cascade` | Exception traversal helper renamed for single-word style. |
| `any_soft_ignorable_exc` | `excusable` | Telegram delete fallback check now uses a single-word name. |
| `chunk_size` | `chunk` | Telegram gateway delete batch parameter converted to one word. |
| `_make_key` | `_stamp` | View factory key helper renamed to a single word. |
| `register_fn` | `enlist` | Factory auto-registration helper renamed to a single word. |
| `_extract_retry_after` | `_delay` | Telegram retry delay helper renamed to a single word. |
| `call_tg` | `invoke` | Telegram retry wrapper now uses a single-word name. |

## Remaining work

The remaining refactors are organised by layer to touch every identifier. Each bullet defines a concrete sweep that should be executed file-by-file until the layer reaches the one-word rule.

### Adapters
- Telegram gateway helpers (`gateway/send.py`, `gateway/edit.py`, `gateway/retry.py`, `gateway/util.py`, `serializer.py`, `media.py`) still expose snake_case functions and temporary variables. Rename each helper to a single concise word, adjusting imports across the package.
- Storage repositories (`storage/*.py`) contain methods such as `get_state`, `save_history`, and `_dump`. Rename the methods and their call sites inside application services so persistence accessors follow the convention.
- Factory registry helpers (`factory/registry.py`) should ensure the new `_stamp` and `enlist` names propagate to every caller and extend the one-word pattern to any remaining utilities.

### Application
- Use case classes and view services rely on helper methods like `_try_dynamic_restore`, `_static_restore_msg`, `_looks_like_file_id`, and `_reply_changed`. Rename those helpers, update all invocations, and adjust any tests using them.
- Mapping utilities in `application/map` should replace identifiers such as `_infer_type` and `_convert_media_item` with one-word names while keeping public API stability.
- Inline strategy logic contains several guard variables (`is_url_input_file`, `strict_inline_media_path`) that should be renamed together with dependency-injection wiring.

### Domain
- Rendering decision helpers (`domain/service/rendering/decision.py` and `helpers.py`) still rely on numerous snake_case helpers; rename each helper and its corresponding references in service callers.
- Ports and repository protocols use snake_case method names (`get_history`, `set_state`, `get_last_id`). Update the protocols, implementations, and use cases to share the new single-word vocabulary.
- Utility modules such as `domain/util/entities.py` and logging modules should revisit helper names (`set_redaction_mode`, `_keys_to_redact`) to match the rule.

### Infrastructure and Presentation
- Dependency injection container attributes (`history_limit`, `strict_inline_media_path`) and presentation layer navigators (`set`, `back`) require renaming to one-word labels, coordinating with configuration constants and UI glue code.
- Tests should mirror every production rename, replacing snake_case fixtures and helper names with the new canonical vocabulary.

Executing the plan in this order keeps surface-level adapters aligned before deep domain contracts are renamed, reducing the blast radius at each iteration and ensuring every identifier eventually reaches the single-word convention.
