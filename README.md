# GenAI Portfolio

Public portfolio of AIDevs Python agent projects — each runnable via Docker Compose with a shared hub mock.

## Status

Agents are being migrated into `apps/`. See individual agent folders for setup and demo instructions.

## Contributing

This repo uses [pre-commit](https://pre-commit.com/) with [gitleaks](https://github.com/gitleaks/gitleaks) to block accidental secret commits.

```sh
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Never commit `.env` files — use `.env.example` as a template.
