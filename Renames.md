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

## Remaining work

Additional modules still use snake_case identifiers. Future steps:

1. Rendering decision helpers should be collapsed or renamed to single-word forms.
2. Configuration objects (e.g., infrastructure settings) require one-word field names.
3. Application service layers include numerous helper variables with underscores that need replacement or refactoring.

This staged approach keeps the codebase functional while progressively moving every identifier to the one-word convention.
