# Review fixes applied (2026-07-07)

Triage of `reviews/impl-review.md` — all 9 findings resolved in code/docs.

## Fixed in code

- F1: `session_manager.py` — session ID allowlist + path containment check
- F2: `voice_agent.py` — redact password turns in logs
- F3: `server.py` + `docker-compose.yml` — `FLASK_HOST` default 127.0.0.1; compose binds localhost
- F6: `shell_agent.py` — `/etc`, `/root`, `/proc` path guardrails
- F7: all `apps/*/package.json` + `hub-mock` — `python -m compileall -q src`; CI adds Python 3.13
- F9: `command_agent.py` — docstring aligned with `.gitignore` learning only

## Fixed in docs

- F4: `PRE-PUBLISH-CHECKLIST.md` — §3 and README table verified; §4/§5 left for pre-push manual gate
- F5: checklist — replaced private path with `<repo-root>`
- F8: `packages/hub-mock/README.md` — full 10-agent route registry

## Pre-push manual gate (unchanged)

Before first public push, still run locally or via CI:

- Docker compose config for all agents (§4)
- GitHub Actions green (§4)
- Clone-fresh smoke test on 3 agents (§5)
- GitHub repo description + branch protection (§6)
