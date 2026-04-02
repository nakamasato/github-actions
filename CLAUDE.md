# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- **JavaScript (pr-description-writer)**:
  - Build: `npm run build` (in pr-description-writer/)
  - Test: `npm test` (runs Jest tests)
  - Single test: `npx jest path/to/test.js`

- **Python (llm-pr-reviewer)**:
  - Install: `poetry install`
  - Test: `poetry run pytest`
  - Single test: `poetry run pytest test_pr_reviwer.py::test_function_name`
  - Lint: `pre-commit run --all-files`

## PR & Commit Convention
- PR title must follow [Conventional Commits](https://www.conventionalcommits.org/) format (release-please uses squash merge titles for changelog)
- Format: `<type>(<scope>): <description>`
  - `scope` should be the component name (e.g., `deploy-cloudrun`, `reusable-workflows`)
- Types: `feat`, `fix`, `chore`, `ci`, `docs`, `refactor`, `test`, `perf`
- Examples:
  - `feat(deploy-cloudrun): add health check option`
  - `fix(pr-description-writer): handle empty body`
  - `chore(deps): update actions/checkout to v5`

## Code Style Guidelines
- **Python**:
  - Formatting: Use ruff-format (enforced via pre-commit)
  - Linting: Use ruff with auto-fix (enforced via pre-commit)
  - Python version: >= 3.12
  - Imports: Group standard library, third-party, and local imports

- **JavaScript**:
  - Use ES6+ features
  - Format with consistent indentation (2 spaces)
  - Use GitHub Actions toolkit for action development
  - Include unit tests for all new functionality
