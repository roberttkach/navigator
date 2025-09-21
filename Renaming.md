# Renaming Plan

## Objectives
- Replace snake_case identifiers with concise single-word alternatives while keeping intent clear.
- Align module names with the one-word rule so imports remain readable and compliant.
- Sequence the work to minimize breakage by starting with leaf utilities before updating shared interfaces.

## Phases
1. **Inventory** – Map every module and identifier that currently relies on underscores or glued words. Use automated search (e.g., `rg "_"`) to capture function, method, and attribute names in batches grouped by feature area (adapters, application, domain, presentation).
2. **Vocabulary Selection** – For each batch, choose precise single-word replacements. Prefer verbs for functions, nouns for classes, and reuse consistent terminology across layers (e.g., repositories use `fetch`/`store`, policies use `allow`, renderers use `render`). Document chosen vocabulary to avoid collisions.
3. **Module Migration** – Rename files and update import paths feature-by-feature. Begin with service helpers (already migrated to `store.preserve/persist/reindex`), then proceed to usecases, adapters, and finally shared domain types. After each module rename, adjust relative imports and run tests.
4. **Interface Refactoring** – Once concrete modules are compliant, refactor ports and adapters so shared interfaces expose single-word APIs. Update adapters, services, and tests in lockstep to avoid dangling references. Stage renames to ensure asynchronous contracts (`fetch`, `store`, `delete`) stay semantically clear.
5. **Validation** – After each phase, execute the full test suite and linting to confirm that renames preserve behavior. Review logs for dynamic attribute access or string-based lookups that may require synchronized updates.

## Next Steps
- Extend the single-word terminology to repository interfaces (`get_history` → `fetch`, `save_history` → `store`, etc.) and propagate changes through adapters and tests.
- Normalize presentation-layer handlers (e.g., `back_handler`) by adopting concise verbs like `back` or `return` while verifying router registrations.
- Audit domain value objects for accessor properties such as `inline_id` and prepare equivalent replacements (e.g., `inline` or `cursor`) alongside serialization adjustments.
- Continue iterating until every identifier, including constants and configuration entries, adheres to the naming rules with no residual underscores apart from private or constant contexts.
