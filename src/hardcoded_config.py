from dataclasses import dataclass
from typing import List

@dataclass
class CrawlerHardcodedConfig:
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER: str
  UNZIP_TO_PERSISTENT_STORAGE_IF_NEWER: str
  UNZIP_TO_PERSISTENT_STORAGE_OVERWRITE: str
  UNZIP_TO_PERSISTENT_STORAGE_CLEAR_BEFORE: str
  LOCALSTORAGE_ZIP_FILENAME_PREFIX: str
  DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES: List[str]


CRAWLER_HARDCODED_CONFIG = CrawlerHardcodedConfig(
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER="domains"
  ,UNZIP_TO_PERSISTENT_STORAGE_IF_NEWER=".unzip_to_persistant_storage_if_newer"
  ,UNZIP_TO_PERSISTENT_STORAGE_OVERWRITE=".unzip_to_persistant_storage_overwrite"
  ,UNZIP_TO_PERSISTENT_STORAGE_CLEAR_BEFORE=".unzip_to_persistant_storage_clear_before"
  ,LOCALSTORAGE_ZIP_FILENAME_PREFIX="download_"
  # https://platform.openai.com/docs/assistants/tools/file-search/supported-files#supported-files
  ,DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES=["c", "cpp", "cs", "css", "doc", "docx", "go", "html", "java", "js", "json", "md", "pdf", "php", "pptx", "py", "rb", "sh", "tex", "ts", "txt"]
)
