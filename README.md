# SC2Helperbot

SC2 Helper Bot is a project to help handling competitive data from StarCraft 2 using Telegram Bot API.

## 1. Inspect the functionalities in a (hopefully) live instance

Check [@SC2Helperbot](https://t.me/SC2Helperbot) in Telegram.

## 2. Setup a local instance

### 2.1 Installing required tools

For running this bot, you will need [python](https://www.python.org/downloads/) and [poetry](https://python-poetry.org/docs/#installation) installed in your system.


### 2.2 Fetching the source code

If you have [git](https://github.com/git-guides/install-git) installed, simply run:

```
$ git clone https://github.com/gvieralopez/SC2Helperbot.git
```

Otherwise, you can download the code from [here](https://github.com/gvieralopez/SC2Helperbot/archive/refs/heads/main.zip). After downloading it, uncompress the file and open a terminal inside the folder you just got.


### 2.3 Installing dependencies

```
$ poetry shell
$ poetry install
$ poetry build
```

### 2.4 Configure the enviroment variables

The main configuration file is `.env`, but it is not distributed with this code. Simply make a copy of `.env.sample` and rename it to `.env`. Edit `.env` with the tha actual values of the enviroment variables:

- `BOT_TOKEN` contains telegram token for your bot (Get it [here](https://t.me/botfather))
- `CONNECTION_STRING` contains the database connection string (e.g., `sqlite:///p/to/db.db`)
- `BLIZZARD_CLIENT_ID` contains your Blizzard client id (Get it [here](https://develop.battle.net/documentation/guides/using-oauth))
- `BLIZZARD_CLIENT_SECRET` contains your Blizzard client secret (Get it [here](https://develop.battle.net/documentation/guides/using-oauth))

- [Optional] `REALM_ID` containing the Blizzard realm id (Default is 1)
- [Optional] `LOG_CHANNEL_ID` containing the Telegram chat where the daily ranking is posted and pinned (Default: not posted)
- [Optional] `DAILY_FETCH_TIME` containing the time of the daily fetch of every user, as `HH:MM` (Default is `17:30`)


### 2.5 Running your own instance

In unix-based systems (Linux, macOS):

```
$ (export $(xargs < .env) && python -m sc2bot)
```

In windows:

```
$ [Coming soon]
```


### 2.6 Bringing the data of the old bot

The old bot (before this rewrite) kept its data in `data/sc2.db` and `data/history/`. To load it into a new, empty database:

```
$ python -m scripts.convert_old_db data/sc2.db data/history sqlite:///p/to/db.db
```

The old history only kept the MMR of each day, so those points take the league, wins, losses and clan of their ladder's last known state.


### 2.7 Importing the full MMR history

[SC2 Pulse](https://sc2pulse.nephest.com/sc2) keeps the 1v1 MMR history of every ranked player. To add it for every player in the database (points already stored are skipped, so it can be run again after new players register):

```
$ python -m scripts.import_pulse_history sqlite:///p/to/db.db
```

History data by [SC2 Pulse](https://sc2pulse.nephest.com/sc2), free for non-commercial use with credit.


## 3. Contributing

Just make a PR.


### Run tests:

```
$ pytest
```

### Type checking:

```
$ mypy
```

### Code style:

```
$ flake8
```
