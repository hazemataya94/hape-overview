import os
import subprocess
import time
from typing import Any, Dict, List, Optional
import requests

from core.logging import LocalLogging
from core.config import Config


class GitLabClient:
    
    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.gitlab_client")
        self.dry_run = True
        self.gitlab_token = Config.get_gitlab_token()
        gitlab_domain = Config.get_gitlab_domain()
        self.gitlab_url = f"https://{gitlab_domain}"

    def git_clone(self, clone_url: str, project_path: str) -> None:
        self.logger.debug(f"git_clone(clone_url: {clone_url}, project_path: {project_path})")
        subprocess.run(["git", "clone", clone_url, project_path], check=True)

    def get_group_projects(self, group_id: int) -> List[Dict[str, Any]]:
        self.logger.debug(f"get_group_projects(group_id: {group_id})")
        headers = {"Private-Token": self.gitlab_token}
        page = 1
        all_projects = []
        while True:
            projects_url = f"{self.gitlab_url}/api/v4/groups/{group_id}/projects"
            params = {
                "include_subgroups": "true",
                "archived": "false",
                "simple": "true",
                "per_page": "100",
                "page": page,
            }
            response = requests.get(projects_url, headers=headers, params=params)
            if response.status_code != 200:
                raise RuntimeError(f"Failed to fetch projects: {response.json().get('message', 'No error message')}")
            projects = response.json()
            if not projects:
                break

            all_projects = all_projects + projects
            page += 1

        return all_projects

    # created_after is in isoformat, e.g. 2026-02-01T00:00:00+00:00
    def get_group_merge_requests(self, group_id: int, created_after: str, state: str = "all", author_username: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.debug(f"get_group_merge_requests(group_id: {group_id}, created_after: {created_after}, state: {state}, author_username: {author_username})")
        headers = {"Private-Token": self.gitlab_token}
        page = 1
        all_merge_requests = []
        while True:
            merge_requests_url = f"{self.gitlab_url}/api/v4/groups/{group_id}/merge_requests"
            params = {
                "include_subgroups": "true",
                "state": state,
                "created_after": created_after,
                "per_page": "100",
                "page": page,
            }
            if author_username:
                params["author_username"] = author_username
            response = requests.get(merge_requests_url, headers=headers, params=params)
            response.raise_for_status()
            merge_requests = response.json()
            if not merge_requests:
                break
            all_merge_requests = all_merge_requests + merge_requests
            page += 1

        return all_merge_requests

    # created_after is in isoformat, e.g. 2026-02-01T00:00:00+00:00
    def get_project_merge_requests(self, project_id: int, created_after: str, state: str = "all", author_username: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.debug(f"get_project_merge_requests(project_id: {project_id}, created_after: {created_after}, state: {state}, author_username: {author_username})")

        headers = {"Private-Token": self.gitlab_token}
        page = 1
        all_merge_requests = []
        while True:
            merge_requests_url = f"{self.gitlab_url}/api/v4/projects/{project_id}/merge_requests"
            params = {
                "state": state,
                "created_after": created_after,
                "per_page": "100",
                "page": page,
            }
            if author_username:
                params["author_username"] = author_username
            response = requests.get(merge_requests_url, headers=headers, params=params)
            response.raise_for_status()
            merge_requests = response.json()
            if not merge_requests:
                break
            all_merge_requests = all_merge_requests + merge_requests
            page += 1

        return all_merge_requests

    def clone_group_projects(self, group_id: int, clone_dir: str) -> None:
        self.logger.debug(f"clone_group_projects(group_id: {group_id}, clone_dir: {clone_dir})")
        projects = self.get_group_projects(group_id)
        for project in projects:
            clone_url = project["ssh_url_to_repo"]
            project_path = os.path.join(clone_dir, project["path_with_namespace"])
            if not os.path.exists(project_path):
                self.logger.info(f"Cloning {project['name']}...")
                time.sleep(2)
                self.git_clone(clone_url, project_path)
            else:
                self.logger.info(f"{project_path} already exists in {clone_dir}. Skipping clone.")
        total_number_of_projects = len(projects)
        self.logger.info(f"Total number of projects: {total_number_of_projects}")
