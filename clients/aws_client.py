import boto3
import os
import time
from botocore.exceptions import ClientError

from core.logging import LocalLogging


class AwsClient:
    def __init__(self, profile_name: str) -> None:
        self.profile_name = profile_name
        self.session = boto3.Session(profile_name=profile_name)
        self.ec2 = self.session.client("ec2")
        self.eks = self.session.client("eks")
        self.autoscaling = self.session.client("autoscaling")
        self.s3 = self.session.client("s3")
        self.region_name = self.session.region_name or self.ec2.meta.region_name
        self.logger = LocalLogging.get_logger("hape.aws_client")
        
    def find_ebs_volume_id_for_pvc(self, pvc_name: str, namespace: str) -> str:
        self.logger.debug(f"find_ebs_volume_id_for_pvc(pvc_name: {pvc_name}, namespace: {namespace})")
        filters = [{"Name": "tag:kubernetes.io/created-for/pvc/name", "Values": [pvc_name]}, {"Name": "tag:kubernetes.io/created-for/pvc/namespace", "Values": [namespace]}]
        response = self.ec2.describe_volumes(Filters=filters)
        volumes = response.get("Volumes", [])
        if not volumes:
            raise RuntimeError(f"No EBS volumes found for PVC '{pvc_name}' in namespace '{namespace}'.")
        if len(volumes) > 1:
            volume_ids = [volume.get("VolumeId") for volume in volumes]
            raise RuntimeError("Multiple EBS volumes found for PVC " f"'{pvc_name}': {volume_ids}. Refine filters or check PVC.")
        volume_id = volumes[0]["VolumeId"]
        return volume_id

    def create_ebs_volume_snapshot(self, volume_id: str, name: str, description: str) -> str:
        self.logger.debug(f"create_ebs_volume_snapshot(volume_id: {volume_id}, name: {name}, description: {description})")
        response = self.ec2.create_snapshot(VolumeId=volume_id, Description=description, TagSpecifications=[{"ResourceType": "snapshot", "Tags": [{"Key": "Name", "Value": name}]}])
        snapshot_id = response["SnapshotId"]
        return snapshot_id

    def get_region_name(self) -> str:
        self.logger.debug("get_region_name()")
        return self.region_name

    def describe_node_group(self, cluster_name: str, node_group_name: str) -> dict:
        self.logger.debug(f"describe_node_group(cluster_name: {cluster_name}, node_group_name: {node_group_name})")
        return self.eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=node_group_name)["nodegroup"]

    def list_node_groups(self, cluster_name: str) -> list[str]:
        self.logger.debug(f"list_node_groups(cluster_name: {cluster_name})")
        paginator = self.eks.get_paginator("list_nodegroups")
        node_groups = []
        for page in paginator.paginate(clusterName=cluster_name):
            node_groups.extend(page.get("nodegroups", []))
        return node_groups

    def wait_for_node_group_status(self, cluster_name: str, node_group_name: str, expected_status: str = "ACTIVE", timeout_seconds: int = 1800, poll_seconds: int = 15) -> dict:
        self.logger.debug(
            f"wait_for_node_group_status(cluster_name: {cluster_name}, node_group_name: {node_group_name}, expected_status: {expected_status}, timeout_seconds: {timeout_seconds}, poll_seconds: {poll_seconds})"
        )
        deadline = time.time() + timeout_seconds
        last_status = "unknown"
        while time.time() < deadline:
            node_group = self.describe_node_group(cluster_name, node_group_name)
            last_status = node_group.get("status", "unknown")
            if last_status == expected_status:
                return node_group
            if last_status in {"CREATE_FAILED", "DEGRADED", "DELETE_FAILED"}:
                raise RuntimeError("Node group reached failure status " f"'{last_status}' for {cluster_name}/{node_group_name}.")
            time.sleep(poll_seconds)
        raise TimeoutError("Timed out waiting for node group status " f"{expected_status} for {cluster_name}/{node_group_name}. " f"Last seen status: {last_status}")

    def wait_for_node_group_absent(self, cluster_name: str, node_group_name: str, timeout_seconds: int = 1800, poll_seconds: int = 15) -> bool:
        self.logger.debug(
            f"wait_for_node_group_absent(cluster_name: {cluster_name}, node_group_name: {node_group_name}, timeout_seconds: {timeout_seconds}, poll_seconds: {poll_seconds})"
        )
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                self.describe_node_group(cluster_name, node_group_name)
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code", "")
                if error_code == "ResourceNotFoundException":
                    return True
                raise
            time.sleep(poll_seconds)
        raise TimeoutError(f"Timed out waiting for node group deletion: " f"{cluster_name}/{node_group_name}.")

    def get_node_group_asgs(self, cluster_name: str, node_group_name: str) -> list[str]:
        self.logger.debug(f"get_node_group_asgs(cluster_name: {cluster_name}, node_group_name: {node_group_name})")
        node_group = self.describe_node_group(cluster_name, node_group_name)
        resources = node_group.get("resources", {})
        autoscaling_groups = resources.get("autoScalingGroups", [])
        return [group.get("name") for group in autoscaling_groups if group.get("name")]

    def get_node_group_desired_size(self, cluster_name: str, node_group_name: str) -> int:
        self.logger.debug(f"get_node_group_desired_size(cluster_name: {cluster_name}, node_group_name: {node_group_name})")
        node_group = self.describe_node_group(cluster_name, node_group_name)
        scaling = node_group.get("scalingConfig", {})
        return int(scaling.get("desiredSize", 0))

    def update_asg_desired_size(self, asg_name: str, desired_size: int) -> None:
        self.logger.debug(f"update_asg_desired_size(asg_name: {asg_name}, desired_size: {desired_size})")
        self.autoscaling.update_auto_scaling_group(AutoScalingGroupName=asg_name, DesiredCapacity=desired_size)

    def get_asg_desired_size(self, asg_name: str) -> int:
        self.logger.debug(f"get_asg_desired_size(asg_name: {asg_name})")
        response = self.autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
        groups = response.get("AutoScalingGroups", [])
        if not groups:
            raise RuntimeError(f"ASG '{asg_name}' not found.")
        return int(groups[0].get("DesiredCapacity", 0))

    def can_access_s3_bucket(self, bucket_name: str) -> bool:
        self.logger.debug(f"can_access_s3_bucket(bucket_name: {bucket_name})")
        try:
            self.s3.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as exc:
            self.logger.error(f"Failed to access S3 bucket {bucket_name}: {exc}")
            return False

    def s3_object_exists(self, bucket_name: str, object_key: str) -> bool:
        self.logger.debug(f"s3_object_exists(bucket_name: {bucket_name}, object_key: {object_key})")
        try:
            self.s3.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise

    def upload_file_to_s3(self, file_path: str, bucket_name: str, object_key: str, overwrite: bool) -> None:
        self.logger.debug(
            f"upload_file_to_s3(file_path: {file_path}, bucket_name: {bucket_name}, object_key: {object_key}, overwrite: {overwrite})"
        )
        if not os.path.exists(file_path):
            raise RuntimeError(f"Local artifact file does not exist: {file_path}")

        if not overwrite and self.s3_object_exists(bucket_name=bucket_name, object_key=object_key):
            raise RuntimeError(f"S3 object already exists and overwrite is disabled: s3://{bucket_name}/{object_key}")

        self.s3.upload_file(file_path, bucket_name, object_key)


if __name__ == "__main__":
    aws_client = AwsClient(profile_name="hape")
    
    cluster_name = "hape"
    node_group_name = "hape-node-group"

    # print("Listing node groups")
    # node_groups = aws_client.list_node_groups(cluster_name=cluster_name)
    # print(node_groups)
    # print("=" * 100)
    # input("Press Enter to continue...")
