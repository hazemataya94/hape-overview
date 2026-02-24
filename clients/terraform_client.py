from typing import TypedDict

from core.logging import LocalLogging
from utils.file_manager import FileManager


class ParsedNodeGroupEntry(TypedDict):
    key: str
    entry_start: int
    entry_end: int
    role: str

class TerraformClient:
    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.terraform_client")
        self.file_manager = FileManager()

if __name__ == "__main__":
    pass