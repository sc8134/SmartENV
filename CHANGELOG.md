# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `py.typed` marker and `MANIFEST.in`, so type checkers see the annotations and
  sdists contain the license, readme, examples, and tests.
- Regression test suite covering imports, copying/pickling, source precedence,
  null handling, BOM handling, and escape sequences.
- CI workflow testing Python 3.10–3.14 on Linux, macOS, and Windows, plus lint,
  formatting, type checking, coverage, and package build jobs.
- Release workflow using PyPI trusted publishing and GitHub Releases.
- Pre-commit hooks, an editor config, and Dependabot updates.
- Contributor documentation: `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, issue forms, and a pull request template.

### Changed

- The PyPI distribution is named `smartenv-settings`; the import package remains
  `smartenv`. PyPI rejects `smartenv` as too similar to the existing
  `smart-env` project.
- Source precedence is now defined by format rather than argument order:
  environment variables > `.env` > TOML > JSON. Within one format, later
  arguments still override earlier ones.
- `get()` and `require()` distinguish a stored `None` from a missing key. A key
  present with value `None` is returned as `None` instead of the default and
  passes `require()`.
- Error messages from `MissingKeyError` list every missing key when several are
  required at once.
- Packaging metadata now declares the conditional `tomli` dependency for
  Python < 3.11 and points at the real repository URLs.

### Fixed

- Import failure on Python 3.10–3.13 caused by PEP 604 unions containing a
  callable in annotations.
- `deepcopy`, `pickle`, and Windows multiprocessing spawn failures caused by
  `__getattr__` running before `_data` exists.
- `.env` files saved with a UTF-8 BOM left the BOM in the first key.
- Quoted values ending in an escaped backslash were parsed as line
  continuations.
- `__contains__` accepted only `str`, violating the `Mapping` contract.
- Unused local imports and inconsistent exception chaining across parsers.

## [1.0.0]

Initial release.

[Unreleased]: https://github.com/sc8134/SmartENV/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sc8134/SmartENV/releases/tag/v1.0.0
