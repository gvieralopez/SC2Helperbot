<div align="center">

<img src="assets/logo.svg" alt="" width="96">

# SC2Helperbot

**A Telegram bot that keeps the StarCraft II ladder stats of a group of friends.**

[![QA](https://github.com/gvieralopez/SC2Helperbot/actions/workflows/qa.yml/badge.svg)](https://github.com/gvieralopez/SC2Helperbot/actions/workflows/qa.yml)
[![Release](https://img.shields.io/github/v/release/gvieralopez/SC2Helperbot?label=release)](https://github.com/gvieralopez/SC2Helperbot/releases/latest)
[![Docker image](https://img.shields.io/badge/docker-ghcr.io-2496ED?logo=docker&logoColor=white)](https://github.com/gvieralopez/SC2Helperbot/pkgs/container/sc2helperbot)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
<br>
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

[Quick start](#quick-start) · [Usage](#usage) · [Configuration](#configuration) · [Data](#data) · [Development](#development)

</div>

---

Register your Battle Tag and the bot finds your StarCraft II profiles, fetches your 1v1 ladders
from Blizzard every day and ranks everyone in the group. A live instance runs as
[@SC2Helperbot](https://t.me/SC2Helperbot).

## Features

- **Ranking.** `/rank` shows the best 1v1 ladder of each user and `/ladders` every ladder, sorted by MMR.
- **Profile.** `/profile` shows your ladders and a chart of your MMR over the last 6 months played.
- **Daily fetch.** Every user's stats are fetched once a day and the ranking is posted and pinned in a log channel.
- **Full history.** Your whole 1v1 career can be imported once from [SC2 Pulse](https://sc2pulse.nephest.com/sc2).

## Quick start

With Docker:

```bash
cp .env.example .env  # Configure as needed
docker run -d --env-file .env -v sc2bot-data:/data \
  -e CONNECTION_STRING=sqlite:////data/sc2bot.db ghcr.io/gvieralopez/sc2helperbot:latest
```

From source:

```bash
uv sync
cp .env.example .env  # Configure as needed
make run
```

## Usage

Text the bot `/register YourName#1234` and it links your StarCraft II profiles; `/link` adds one by its
starcraft2.com URL. Then `/fetch`, `/profile`, `/rank`, `/ladders` and `/users`; `/help` lists them all
and `/help <command>` explains one. In a group, `/rank@SC2Helperbot` and `/help_fetch` work too.

## Configuration

Environment variables (see `.env.example`):

- `BOT_TOKEN`: the Telegram token of your bot (get it from [BotFather](https://t.me/botfather)).
- `CONNECTION_STRING`: the database connection string, e.g. `sqlite:///p/to/db.db`.
- `BLIZZARD_CLIENT_ID` and `BLIZZARD_CLIENT_SECRET`: your Blizzard API client (get it [here](https://develop.battle.net/documentation/guides/using-oauth)).
- [Optional] `REALM_ID`: the Blizzard realm id (default `1`).
- [Optional] `LOG_CHANNEL_ID`: the Telegram chat where the daily ranking is posted and pinned (default: not posted).
- [Optional] `DAILY_FETCH_TIME`: the time of the daily fetch of every user, as `HH:MM` (default `17:30`).

## Data

### Bringing the data of the old bot

The old bot (before the 2022 rewrite) kept its data in `data/sc2.db` and `data/history/`. To load it into a new, empty database:

```bash
uv run python -m scripts.convert_old_db data/sc2.db data/history sqlite:///p/to/db.db
```

The old history only kept the MMR of each day, so those points take the league, wins, losses and clan of their ladder's last known state.

### Importing the full MMR history

[SC2 Pulse](https://sc2pulse.nephest.com/sc2) keeps the 1v1 MMR history of every ranked player. To add it for every player in the database (points already stored are skipped, so it can be run again after new players register):

```bash
uv run python -m scripts.import_pulse_history sqlite:///p/to/db.db
```

History data by [SC2 Pulse](https://sc2pulse.nephest.com/sc2), free for non-commercial use with credit.

## Development

Setup, QA and releases: [DEVELOPMENT.md](DEVELOPMENT.md).

## Contributing

Issues and pull requests are welcome; `make qa` must pass.

## License

MIT: see [LICENSE](LICENSE).

---

<sub>🚀 Project starter provided by [Cookie Pyrate v1.0.3](https://github.com/gvieralopez/cookie-pyrate/tree/v1.0.3)</sub>
