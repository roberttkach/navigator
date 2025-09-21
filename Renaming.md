# Renaming Plan

## Objectives
- Ensure every identifier uses a single, meaningful word.
- Avoid underscores outside of leading underscores and existing constants.
- Prefer short, precise terms that preserve intent.

## Completed Adjustments
- Telegram router handlers now expose the callback handler as `retreat` and the text handler as `recall`, with `_tongue` providing locale detection.
- Telegram scope builder renamed to `outline`, imported through the composition root as `forge`.
- Navigator tail helper now relies on `_tailer` and uses `identifier`/`status` for clarity when referencing message identifiers and state values.

## Next Steps
- Migrate remaining domain and application layer functions (for example `get_history`, `save_history`, `log_io`) to single-word equivalents while keeping semantic clarity.
- Replace abbreviations such as `uc`, `msg`, `cfg`, and similar throughout the repository with full words.
- Audit adapter-layer gateway helpers (e.g., `do_edit_text`, `reply_for_send`) and select concise replacements that respect the single-word rule.
- Review protocol definitions so that method names like `get_state`, `set_state`, and `save_history` become single-word verbs without losing intent (e.g., `state`, `store`).

## Guidelines for Future Renames
- When multiple contexts share similar operations, choose consistent vocabulary (e.g., prefer `store`/`load` across repositories).
- Use existing domain terminology (history, tail, scope, ledger) to inform replacement words instead of inventing artificial compounds.
- Validate each rename with type checkers or runtime smoke tests to avoid behavioural regressions.
