# Renaming Plan

## Classes
- `MessageEditForbidden` → `EditForbidden`: trims the class name to two words while keeping the intent of an edit ban clear.
- `MessageNotChanged` → `MessageUnchanged`: restates the outcome with two words and avoids the long construct.
- `TextTooLong` → `TextOverflow`: captures the breach of text length with a concise two-word name.
- `CaptionTooLong` → `CaptionOverflow`: mirrors the text rename for caption length excess.
- `ExtraKeyForbidden` → `ExtraForbidden`: shortens the prohibition message to two words.
- `MediaGroupInvalid` → `AlbumInvalid`: keeps the album validation failure precise with two words.
- `_RedisLockAdapter` → `_RedisLatch`: shortens the helper class to two meaningful words while preserving the private prefix.
- `RenderResultNode` → `RenderNode`: reduces the tree node wrapper to two words without losing meaning.

## Functions and Methods
- `swap_inline` → `inline`: gives the inline-only entry point a single-word verb that reflects its focus.

## Parameters
- `include_topic` → `topical`: replaces the multi-word flag with a single adjective describing the option.

## Local Variables
- `screened_effect` → `addition`: emphasises the supplemental filtered payload with one word.
- `raw_id` → `raw`: marks the unparsed identifier succinctly.
- `message_id` → `ident`: denotes the parsed identifier without an underscore.
- `extras_raw` → `source`: labels the raw extras list with a single descriptive word.

This plan has been fully applied across the codebase so that identifiers now adhere to the requested naming rules.
