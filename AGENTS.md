# Repository Guidelines

## Project Structure

- `core/` contains the Python engine for speech, conversation, tasks, memory, and sync. `ui/` contains the desktop shell and web UI, including Studio modules in `ui/studio/` and shared assets in `ui/assets/`.
- `android/src/` contains the Java bridge and services. Edit Android app JavaScript in `android/www-src/app/` and run `python3 tools/app_join.py` to regenerate `android/assets/www/app.js`.
- `server/` contains self-hosted speech services. `packaging/` and `tools/` contain installers and build scripts. Look in `data/` and `icons/` for bundled data and artwork, and in `tests/fixtures/` for test data.

## Build, Test, and Development

Run these commands from the repository root. Use Bash for the shell scripts.

- `python3 -m pip install -r requirements.txt -r requirements-extra.txt` installs Python dependencies.
- `python3 core/main.py` starts the engine. `python3 ui/app.py` opens the desktop UI.
- `bash tests/run_quick.sh` runs the CI suite. `bash tests/run_changed.sh` selects checks affected by your changes. `bash tests/run_all.sh` adds audio and model scenarios and requires Playwright with Chromium, `espeak-ng`, and `ffmpeg`.
- `bash tools/build_deb.sh dist` builds the Linux package. `bash tools/build_win.sh` builds the Windows installer. `bash android/tools/build_apk.sh --check` checks the Android build without a signing key.

## Coding Style

Follow `.editorconfig` for UTF-8, LF, and four-space indentation by default. Use two spaces for JavaScript, HTML, CSS, JSON, YAML, and XML. Use `snake_case` for Python functions and `camelCase` for JavaScript functions. Write comments in Russian and explain constraints or intent. For comment-only edits, use `python3 tools/check_comments.py` to check for code changes. The quick suite checks Python syntax and runs `node --check` when Node.js is available.

## Testing Guidelines

Cover fixes and new behavior with standalone scripts named `*_test.py`. Run a focused check with `python3 tests/unit_test.py`. Use Playwright for browser flows. Register new tests in `tests/run_all.sh` and fast tests in `tests/run_quick.sh`. See [docs/TESTS.md](docs/TESTS.md).

## Commits and Pull Requests

Use `origin/main` as the fork's integration branch. Start `feature/*` branches for your changes and `import/*` branches for upstream changes from an up-to-date `main`.

Run `git fetch upstream` and `git log --oneline --right-only --cherry-pick main...upstream/main` to review the author's releases. Use `git cherry-pick -x SHA` for a whole commit. For a release that bundles several changes, port the files or hunks you need, check their dependencies, and record the source SHA.

Open PRs against the fork's `main`. Describe the change and verification, link issues, and add screenshots where useful. See [CONTRIBUTING.md](CONTRIBUTING.md) for upstream contributions.
