ERROR_MESSAGES = {
    "CONFIG_PERMISSION_DENIED": "Permission denied creating '{parent_dir}'. Use --config-file-path with a writable location.",
    "CONFIG_ENV_FILE_INVALID": "Unable to load .env file: {dot_env_file}",
    "CONFIG_ENV_KEY_REQUIRED": "{config_key} must be set in .env.",
    "CONFIG_ENV_INT_REQUIRED": "{config_key} must be an integer in .env.",
}


def get_config_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown config error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_config_error_message("CONFIG_PERMISSION_DENIED", parent_dir="/tmp"))
