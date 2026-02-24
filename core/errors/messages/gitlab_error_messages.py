ERROR_MESSAGES = {
    "GITLAB_CREATED_AFTER_REQUIRED": "created_after is required (dd.mm.yyyy, dd-mm-yyyy, or dd/mm/yyyy).",
    "GITLAB_GROUP_OR_PROJECT_REQUIRED": "Either group_id or project_id must be provided.",
    "GITLAB_GROUP_AND_PROJECT_EXCLUSIVE": "Use only one of group_id or project_id.",
    "GITLAB_INVALID_CREATED_AFTER": "created_after has an invalid format: {created_after}",
    "GITLAB_CLONE_FAILED": "Failed to clone GitLab projects for group_id={group_id}.",
    "GITLAB_GET_GROUP_PROJECTS_FAILED": "Failed to fetch GitLab group projects for group_id={group_id}.",
    "GITLAB_GET_GROUP_MR_FAILED": "Failed to fetch GitLab merge requests for group_id={group_id}.",
    "GITLAB_GET_PROJECT_MR_FAILED": "Failed to fetch GitLab merge requests for project_id={project_id}.",
}


def get_gitlab_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown GitLab error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_gitlab_error_message("GITLAB_GROUP_OR_PROJECT_REQUIRED"))
