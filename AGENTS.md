# Agent Instructions

This repository is intended to be worked by automated coding agents as well as humans. Agents must treat these instructions as mandatory unless a user explicitly overrides them in the current task.

## Git Workflow

- Create a dedicated git branch for every code, documentation, configuration, or test change.
- Use descriptive branch names with the `codex/` prefix for Codex work, such as `codex/backend-api-foundation` or `codex/playwright-scraper`.
- Keep each branch focused on one task from `TODO.md` whenever possible.
- Do not work directly on `main`.
- Integrate completed and validated work into the `staging` branch.
- If `staging` does not exist, create it from the current `main` branch before the first integration.
- After a task is complete, merge the task branch into `staging` only after tests pass and the relevant `TODO.md` item is marked complete.
- Keep `main` stable. Promote `staging` to `main` only when the user explicitly requests a release or production merge.

## Quality Bar

- Add or update tests for every behavior change.
- Run focused tests before finishing any task.
- Run broader validation when a change touches shared contracts, persistence, scraping behavior, API shape, or frontend workflows.
- Do not mark a task complete until the implementation, tests, and documentation all match the requested behavior.
- Prefer simple, explicit code over clever abstractions.
- Preserve existing behavior unless the current task intentionally changes it.

## Project Direction

- Build a Python + React news scraping system.
- Use FastAPI for the backend API.
- Use Playwright Python for browser-based website scraping and article extraction.
- Use React for the admin frontend.
- Provide backend APIs for all frontend and scraping operations.
- Keep scraping logic testable outside the API layer.

## TODO Discipline

- Treat `TODO.md` as the source of implementation tasks for dev_pipeline runs.
- Work one unchecked task at a time unless the user asks for a larger batch.
- Mark a `TODO.md` task as `[x]` only after the task is implemented and verified.
- If a task is blocked, leave it unchecked and document the blocker in the final response or a follow-up note.
- Keep checklist task titles unique so automation can identify completed items reliably.

## Expected Verification

- Backend changes should include API and service tests.
- Scraper changes should include parser or extractor tests, plus mocked or fixture-backed Playwright coverage where practical.
- Frontend changes should include component, interaction, or end-to-end tests depending on the risk of the change.
- Documentation-only changes should be checked for consistency with `PROJECT.md`, `ROADMAP.md`, and `TODO.md`.
