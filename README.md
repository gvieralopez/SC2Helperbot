# SC2Bot

## Project build

```
$ poetry shell
$ poetry install
$ poetry build
```

## Run Pytests

```
$ pytest
```

## Mypy

```
$ mypy
```

## Flake8

```
$ flake8
```

## Run locally
You need to set the following environment variables:
- `BOT_TOKEN` containing the telegram token for the bot
- `CONNECTION_STRING` containing the database connection string
- `BLIZZARD_CLIENT_ID` containing the Blizzard client id
- `BLIZZARD_CLIENT_SECRET` containing the Blizzard client secret
- [Optional] `REALM_ID` containing the Blizzard realm id

There is an example of [`.env` file](.env.sample) you could use as a template
to create your own .env file with the actual values of your variables.

```
$ python -m sc2bot
```
