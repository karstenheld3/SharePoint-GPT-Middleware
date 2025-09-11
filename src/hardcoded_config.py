from dataclasses import dataclass

@dataclass
class CrawlerHardcodedConfig:
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER: str
  UNZIP_TO_PERSISTENT_STORAGE_IF_NEWER: str
  UNZIP_TO_PERSISTENT_STORAGE_OVERWRITE: str

CRAWLER_HARDCODED_CONFIG = CrawlerHardcodedConfig(
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER="domains"
  ,UNZIP_TO_PERSISTENT_STORAGE_IF_NEWER=".unzip_to_persistant_storage_if_newer"
  ,UNZIP_TO_PERSISTENT_STORAGE_OVERWRITE=".unzip_to_persistant_storage_overwrite"
)
