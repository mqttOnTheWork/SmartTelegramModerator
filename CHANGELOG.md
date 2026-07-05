# Changelog

All notable changes to this project are documented here. The project follows
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-05

First stable release. The bot now covers the full moderation pipeline end to end.

### Added
- Monitoring: Prometheus metrics and a `/metrics` endpoint; Prometheus and
  Grafana services in `docker-compose`.
- Final documentation and changelog.

## [0.9.0] - 2026-07-05
### Added
- Dockerfile, `docker-compose` (API + PostgreSQL + Redis), and GitHub Actions CI
  (lint, tests, Docker build).

## [0.8.0] - 2026-07-04
### Added
- Web dashboard with a moderation stats page and JSON endpoint.

## [0.7.0] - 2026-07-04
### Added
- REST API on FastAPI with JWT authentication and role checks.

## [0.6.0] - 2026-07-03
### Added
- Moderation actions: warnings with escalation, mutes, bans, reputation, roles.

## [0.5.0] - 2026-07-03
### Added
- ML pipeline: toxicity training and inference with a heuristic fallback.

## [0.4.0] - 2026-07-02
### Added
- Moderation engine with link, profanity, advertising, repeat-spam and flood
  filters.

## [0.3.0] - 2026-07-01
### Added
- Telegram bot skeleton and command handlers.

## [0.2.0] - 2026-07-01
### Added
- Data layer: PostgreSQL models (SQLAlchemy async) and a Redis client.

## [0.1.0] - 2026-06-30
### Added
- Project scaffold: configuration, logging, exceptions, and tests.
