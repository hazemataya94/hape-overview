from pathlib import Path


def print_artifacts_directory(artifacts_directory: Path) -> None:
    print("\n")
    print("-" * 80)
    print("Artifacts directory")
    print(artifacts_directory)
    print("-" * 80)


if __name__ == "__main__":
    print_artifacts_directory(Path("/tmp/example-artifacts"))
