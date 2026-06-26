# Smart Telegram Moderator AI

An intelligent Telegram bot for automatic group moderation, powered by ML/NLP.

The project brings together Machine Learning, NLP, the Telegram Bot API, FastAPI,
PostgreSQL, Redis, Docker, CI/CD, a web dashboard, structured logging, a role
system, and a scalable architecture.

## Features

- Automatic message moderation: anti-spam, anti-flood, anti-advertising,
  profanity, toxicity, insults, threats, and phishing.
- Attachment analysis: links, images, video, voice, documents, stickers, GIFs.
- Warnings, mutes, and bans with configurable thresholds.
- User reputation and a role system (admins / users).
- ML inference for text classification (toxicity / spam) plus model training.
- REST API (FastAPI) with JWT auth and a web dashboard.
- PostgreSQL for storage, Redis for caching and rate limiting.
- Full logging, monitoring (Prometheus / Grafana), and backups.

## Tech stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Language     | Python 3.12                         |
| Bot          | aiogram (Telegram Bot API, async)   |
| API          | FastAPI + Uvicorn                   |
| Database     | PostgreSQL + SQLAlchemy (async)     |
| Cache        | Redis                               |
| ML / NLP     | scikit-learn / transformers         |
| Containers   | Docker + Docker Compose             |
| CI/CD        | GitHub Actions                      |
| Monitoring   | Prometheus + Grafana                |
| Tests        | pytest (coverage >= 80%)            |

## Engineering principles

- SOLID, strict Python typing, async where it makes sense.
- Configuration via `.env`, full logging, and thorough exception handling.
- Test coverage of at least 80%.
- Resilience: connection loss, retries, Telegram API limits, database/Redis
  outages, and model errors.

## Project layout

```
smart-telegram-moderator/
├── app/
│   ├── core/            # configuration, logging, exceptions
│   ├── db/              # PostgreSQL models and sessions
│   ├── cache/           # Redis client
│   ├── bot/             # Telegram bot and command handlers
│   ├── moderation/      # rules engine and filters
│   ├── ml/              # ML pipeline (training / inference)
│   ├── services/        # warnings, mutes, bans, reputation, roles
│   └── api/             # FastAPI REST API + auth
├── dashboard/           # web dashboard
├── tests/               # unit / integration / e2e
├── docker/              # Dockerfile and configs
├── .github/workflows/   # CI/CD pipelines
└── docs/                # documentation, plan, diagrams
```

## Getting started

```bash
# 1. Virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 2. Dependencies
pip install -r requirements.txt

# 3. Configuration
copy .env.example .env        # then fill in the values (bot token, DB, etc.)

# 4. Run the bot
python -m app.main
```

## Bot commands

| Command  | Description                                        |
|----------|----------------------------------------------------|
| `/start` | start the bot and show a greeting                  |
| `/help`  | list available commands                            |
| `/warn`  | warn a user (reply to their message)               |
| `/mute`  | temporarily restrict a user, e.g. `/mute 30m`      |
| `/ban`   | ban a user from the chat                           |
| `/stats` | show moderation statistics for the chat            |

## Running with Docker

```bash
docker compose up --build
```

This starts the API and dashboard (port 8000), PostgreSQL, Redis, Prometheus
(port 9090) and Grafana (port 3000).

## Monitoring

The API exposes Prometheus metrics at `/metrics`: processed messages by verdict,
moderation actions by type, and model inference latency. Prometheus scrapes them
and Grafana visualises the data.

## Documentation

- Roadmap: [`docs/PLAN.md`](docs/PLAN.md)
- Changelog: [`CHANGELOG.md`](CHANGELOG.md) (also [`ИСТОРИЯ.md`](ИСТОРИЯ.md) in Russian)

## License

[MIT](LICENSE)
