# Renaming Plan

## Scope
This iteration covers the Telegram gateway deletion workflow.

## Renamed identifiers
- Module `adapters.telegram.gateway.delete` → `adapters.telegram.gateway.purge` (file renamed to keep a single-word, action-focused title).
- Class `DeleteBatch` → `PurgeTask` (single, precise wording for the gateway purge coordinator).
- Method `DeleteBatch.run` → `PurgeTask.execute` (verb retained as a single descriptive word).
- Local import alias `_order` → `arrange` (single clear word without a leading underscore).
- Local list name `groups` → `batches` (single word that matches the semantics of chunked message groups).
- Telegram gateway attribute `_delete` → `_purge` and its usage within `TelegramGateway.delete` (aligns with the new class name while keeping the private attribute prefix).
- Trial helper instantiation `DeleteBatch` → `PurgeTask` within `trial.py` (keeps test coverage aligned with the rename).

## Follow-up
Further iterations can extend this naming pass to the rest of the adapters package and the remaining application layers.
