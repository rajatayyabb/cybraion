# Contributing to Cybraion

Thank you for helping improve Cybraion. It is a research and education project for deterministic authorization around AI-agent tool calls.

## Before opening an issue

- Search existing issues first.
- Reproduce the problem with the smallest safe example.
- Never include credentials, tokens, personal data, or real customer records.
- Describe the expected decision (`ALLOW`, `BLOCK`, or `REQUIRE_APPROVAL`) and the actual result.

## Pull requests

1. Fork the repository and create a focused branch.
2. Keep changes small and explain the security impact.
3. Add or update tests for policy-engine behavior.
4. Run `pytest -q` locally.
5. Update the README or changelog when behavior or public APIs change.

## Safety boundary

Use Cybraion only with systems, agents, data, and tools you own or are explicitly authorized to test. Do not submit exploit payloads, secrets, or private data in issues or pull requests.
