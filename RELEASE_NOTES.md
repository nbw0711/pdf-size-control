# v1.0.0 — PDF Size Control

- Local batch PDF compression with a manually entered per-file MB limit, including decimals.
- English, Simplified Chinese, Traditional Chinese and Japanese interfaces, application messages and logs.
- Original-file preservation, unique output names, progress logs, cancellation and JSON reports.
- Standalone macOS Apple Silicon app and portable Windows x64 EXE bundle; no Python setup needed.
- Source code and reproducible build scripts under the MIT license.

Validation: the macOS standalone app passed four-language GUI and real compression self-tests using generated PDFs. The Windows package passed runtime checksum, EXE architecture, dependency and archive checks, but has not yet been executed on Windows hardware.

The macOS app is locally signed, not Apple notarized. Windows requires extracting the entire package and retaining its runtime/app folders. Lossy compression may reduce quality; unattainable size limits are reported.
