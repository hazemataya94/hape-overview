from collections import Counter
from typing import Any, Dict, List, Optional

from clients.gitlab_client import GitLabClient
from core.errors.exceptions import HapeExternalError, HapeValidationError
from core.errors.messages.gitlab_error_messages import get_gitlab_error_message
from core.logging import LocalLogging
from utils.datetime_utils import DatetimeUtils


class GitLabService:
    def __init__(self, gitlab_client: Optional[GitLabClient] = None) -> None:
        self.gitlab_client = gitlab_client or GitLabClient()
        self.logger = LocalLogging.get_logger("hape.gitlab_service")

    def clone_group_projects(self, group_id: int, clone_dir: str) -> None:
        self.logger.debug(f"clone_group_projects(group_id={group_id}, clone_dir={clone_dir})")
        try:
            self.gitlab_client.clone_group_projects(group_id, clone_dir)
        except Exception as exc:
            raise HapeExternalError(
                code="GITLAB_CLONE_FAILED",
                message=get_gitlab_error_message(
                    "GITLAB_CLONE_FAILED",
                    group_id=group_id,
                ),
            ) from exc
        self.logger.info(
            f"clone_group_projects completed for group_id={group_id}"
        )

    def get_group_projects(self, group_id: int) -> List[Dict[str, Any]]:
        self.logger.debug(f"get_group_projects(group_id={group_id})")
        try:
            return self.gitlab_client.get_group_projects(group_id)
        except Exception as exc:
            raise HapeExternalError(
                code="GITLAB_GET_GROUP_PROJECTS_FAILED",
                message=get_gitlab_error_message(
                    "GITLAB_GET_GROUP_PROJECTS_FAILED",
                    group_id=group_id,
                ),
            ) from exc

    def get_group_merge_requests(self, group_id: int, created_after: str, state: str = "all", author_username: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.debug(f"get_group_merge_requests(group_id={group_id}, created_after={created_after}, state={state}, author_username={author_username})")
        if not created_after or not created_after.strip():
            raise HapeValidationError(
                code="GITLAB_CREATED_AFTER_REQUIRED",
                message=get_gitlab_error_message("GITLAB_CREATED_AFTER_REQUIRED"),
            )
        try:
            created_after_normalized = DatetimeUtils.normalize_date_format(created_after)
        except ValueError as exc:
            raise HapeValidationError(
                code="GITLAB_INVALID_CREATED_AFTER",
                message=get_gitlab_error_message(
                    "GITLAB_INVALID_CREATED_AFTER",
                    created_after=created_after,
                ),
            ) from exc
        created_after_isoformat = DatetimeUtils.date_to_isoformat(created_after_normalized)

        try:
            merge_requests = self.gitlab_client.get_group_merge_requests(
                group_id=group_id,
                created_after=created_after_isoformat,
                state=state,
                author_username=author_username,
            )
        except Exception as exc:
            raise HapeExternalError(
                code="GITLAB_GET_GROUP_MR_FAILED",
                message=get_gitlab_error_message(
                    "GITLAB_GET_GROUP_MR_FAILED",
                    group_id=group_id,
                ),
            ) from exc
        self.logger.debug(f"get_group_merge_requests fetched {len(merge_requests)} merge requests for group_id={group_id}")
        return merge_requests

    def count_merge_requests_per_day(self, created_after: str, group_id: Optional[int] = None, project_id: Optional[int] = None, username: Optional[str] = None) -> Counter[str]:
        self.logger.debug(f"count_merge_requests_per_day(created_after={created_after}, group_id={group_id}, project_id={project_id}, username={username})")
        if group_id is not None and project_id is not None:
            raise HapeValidationError(
                code="GITLAB_GROUP_AND_PROJECT_EXCLUSIVE",
                message=get_gitlab_error_message("GITLAB_GROUP_AND_PROJECT_EXCLUSIVE"),
            )

        if group_id is None and project_id is None:
            raise HapeValidationError(
                code="GITLAB_GROUP_OR_PROJECT_REQUIRED",
                message=get_gitlab_error_message("GITLAB_GROUP_OR_PROJECT_REQUIRED"),
            )
        if not created_after or not created_after.strip():
            raise HapeValidationError(
                code="GITLAB_CREATED_AFTER_REQUIRED",
                message=get_gitlab_error_message("GITLAB_CREATED_AFTER_REQUIRED"),
            )
        try:
            created_after_normalized = DatetimeUtils.normalize_date_format(created_after)
        except ValueError as exc:
            raise HapeValidationError(
                code="GITLAB_INVALID_CREATED_AFTER",
                message=get_gitlab_error_message(
                    "GITLAB_INVALID_CREATED_AFTER",
                    created_after=created_after,
                ),
            ) from exc

        if project_id is not None:
            created_after_isoformat = DatetimeUtils.date_to_isoformat(created_after_normalized)
            try:
                merge_requests = self.gitlab_client.get_project_merge_requests(
                    project_id=project_id,
                    created_after=created_after_isoformat,
                    state="all",
                    author_username=username,
                )
            except Exception as exc:
                raise HapeExternalError(
                    code="GITLAB_GET_PROJECT_MR_FAILED",
                    message=get_gitlab_error_message(
                        "GITLAB_GET_PROJECT_MR_FAILED",
                        project_id=project_id,
                    ),
                ) from exc
        else:
            merge_requests = self.get_group_merge_requests(
                group_id=group_id,
                created_after=created_after_normalized,
                state="all",
                author_username=username,
            )

        created_dates: List[str] = []
        for merge_request in merge_requests:
            created_at = merge_request.get("created_at")
            if not created_at:
                continue
            created_date = DatetimeUtils.parse_iso_datetime(created_at).date().isoformat()
            created_dates.append(created_date)

        counts = Counter(created_dates)
        self.logger.info(f"count_merge_requests_per_day completed with {sum(counts.values())} merge requests across {len(counts.keys())} days")
        return counts

