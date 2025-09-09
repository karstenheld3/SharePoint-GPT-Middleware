from dataclasses import dataclass

@dataclass
class CrawlerHardcodedConfig:
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER: str

CRAWLER_HARDCODED_CONFIG = CrawlerHardcodedConfig(
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER="domains"
)
