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


### 2.5 Running your own instance

In unix-based systems (Linux, macOS):

```
$ (source .env && python -m sc2bot)
```

In windows:

```
$ [Coming soon]
```


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