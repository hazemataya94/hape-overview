ERROR_MESSAGES = {
    "KUBERNETES_LIST_CONTEXTS_FAILED": "Failed to list Kubernetes contexts.",
    "KUBERNETES_EXTRACT_ESO_FAILED": "Failed to extract ExternalSecrets resources.",
}


def get_kubernetes_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown Kubernetes error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_kubernetes_error_message("KUBERNETES_LIST_CONTEXTS_FAILED"))
