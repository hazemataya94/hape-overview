# Configuration

## Overview
Command configuration values are read from environment variables (including `.env`) first, then `config.json`.
Logging settings still use environment variables (`HAPE_LOG_LEVEL`, `HAPE_ENABLE_LOG_FILE`, `HAPE_LOG_FILE`).

Default path:
```
~/.hape/config.json
```

You can override the config path per command:
```
hape --config-file-path /path/to/config.json <command>
```

## Generate config.json
Use the config command to generate the JSON file from environment variables.
To load values from a `.env` file, pass `--dot-env-file`.
```
hape config init-config-file
hape config init-config-file --dot-env-file /path/to/.env
```

This overwrites any existing config file at the target path.

## Keys
All config keys are optional in `config.json`.
Commands fail only when they read a key that is missing.

General keys:
- `DEPLOYMENTS_ROOT`

Logging keys (environment-based):
- `HAPE_LOG_LEVEL` (one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`; default `DEBUG`)
- `HAPE_ENABLE_LOG_FILE` (0/1 or true/false; default `0`)
- `HAPE_LOG_FILE` (path for log file when file logging is enabled; default `~/.hape/hape.log`)

GitLab keys:
- `GITLAB_DOMAIN`
- `GITLAB_TOKEN`
- `GITLAB_DEFAULT_GROUP_ID`

Atlassian keys:
- `ATLASSIAN_DOMAIN`
- `ATLASSIAN_EMAIL`
- `ATLASSIAN_API_KEY`
- `CONFLUENCE_CHANGELOG_PARENT_PAGE_ID`
- `CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID`
- `CONFLUENCE_TEST_PARENT_PAGE_ID`

Integer keys (when present):
- `GITLAB_DEFAULT_GROUP_ID`
- `CONFLUENCE_CHANGELOG_PARENT_PAGE_ID`
- `CONFLUENCE_CHANGELOG_ENTRY_PAGE_TEMPLATE_ID`
- `CONFLUENCE_TEST_PARENT_PAGE_ID`
