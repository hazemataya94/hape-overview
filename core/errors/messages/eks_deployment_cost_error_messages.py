ERROR_MESSAGES = {
    "EDC_KUBE_CONTEXT_REQUIRED": "Kubernetes context is required.",
    "EDC_AWS_PROFILE_REQUIRED": "AWS profile is required.",
    "EDC_OUTPUT_DIR_REQUIRED": "Output directory is required.",
    "EDC_TOP_N_INVALID": "Top N must be a positive integer.",
    "EDC_RESOURCE_TYPES_INVALID": "Unsupported resource types: {resource_types}. Allowed values are: {allowed_resource_types}.",
    "EDC_NAMESPACES_INVALID": "Namespaces flag format is invalid.",
    "EDC_KUBERNETES_READ_FAILED": "Failed to read Kubernetes workloads for cost report.",
    "EDC_INSTANCE_TYPE_DERIVE_FAILED": "Failed to derive EC2 instance type from running pods metadata for {resource_type} '{namespace}/{name}'.",
    "EDC_AWS_PRICING_LOOKUP_FAILED": "Failed to lookup AWS pricing details for instance type '{instance_type}' in region '{region}'.",
    "EDC_REPORT_WRITE_FAILED": "Failed to write EKS deployment cost report outputs to '{output_dir}'.",
}


def get_eks_deployment_cost_error_message(message_key: str, **kwargs: str) -> str:
    template = ERROR_MESSAGES.get(message_key, "Unknown EKS deployment cost error.")
    return template.format(**kwargs)


if __name__ == "__main__":
    print(get_eks_deployment_cost_error_message("EDC_TOP_N_INVALID"))
