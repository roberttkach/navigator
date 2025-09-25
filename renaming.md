# Renaming Plan

## Objectives
- Standardize every identifier (variables, attributes, functions, classes, modules, files) to a single clear word (classes may use two) without internal underscores, following the project directive.
- Preserve semantic clarity while favoring the shortest accurate term.
- Execute changes incrementally to maintain reviewability and runtime stability.

## Process Overview
1. **Inventory** – Traverse each package (`presentation`, `app`, `core`, `bootstrap`, `infra`, `adapters`, `api`, `entrypoints`) and log identifiers containing inner underscores or multi-word constructs.
2. **Classification** – Group findings by role (class, function, constant, field) to decide replacement vocabulary consistent within each domain.
3. **Vocabulary Selection** – For each group choose canonical replacements (e.g., telemetry helpers → `report`, payload builders → `bundle`, dictionary constants → `LEXICON`). Validate that the chosen word is already meaningful in the code base or in the business domain.
4. **Dependency Check** – Map cross-module references to schedule refactors in dependency order (values → services → presentation) preventing broken imports.
5. **Incremental Refactors** – Rename identifiers module by module, running the full test suite after each package batch. Prefer smaller commits scoped to a package to aid review.
6. **Verification** – Use static analysis and runtime checks (imports, unit tests) to confirm no stale references remain. Run linters/formatters if configured.
7. **Documentation Update** – Adjust any prose, comments, or configuration referencing legacy names, ensuring instructions and public APIs match the new vocabulary.

## Completed Step in This Iteration
- Converted the presentation telemetry helper identifiers to single-word names (`_TailView`, `_bundle`, `_report`, `_profile`) and normalized the alerts lexicon constant to `LEXICON` as an initial template for subsequent packages.

## Next Targets
- **Application layer (`app`)**: rename payload assembly helpers and DTO fields that currently use snake_case or compound words.
- **Core services**: align telemetry and scope utilities with the new naming vocabulary to avoid mismatched helper terms.
- **Bootstrap and entrypoints**: ensure configuration keys and exposed API objects follow the single-word guideline.
- **File names**: audit every module path to replace multi-word snake_case files with concise single-word equivalents.

Progress will continue package by package until the entire project adheres to the naming convention.
