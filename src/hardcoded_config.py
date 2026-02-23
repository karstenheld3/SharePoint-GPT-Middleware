from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class CrawlerHardcodedConfig:
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER: str
  PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER: str
  PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER: str
  PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER: str
  PERSISTENT_STORAGE_PATH_TEMP_SUBFOLDER: str
  PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER: str
  PERSISTENT_STORAGE_PATH_LISTS_FOLDER: str
  PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER: str
  PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER: str
  PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER: str
  PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER: str
  PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE: int
  FILES_METADATA_JSON: str
  DOMAIN_JSON: str
  SITE_JSON: str
  SHAREPOINT_MAP_CSV: str
  SHAREPOINT_ERROR_MAP_CSV: str
  FILE_MAP_CSV: str
  FILE_FAILED_MAP_CSV: str
  VECTOR_STORE_MAP_CSV: str
  UNZIP_TO_PERSISTENT_STORAGE_IF_NEWER: str
  UNZIP_TO_PERSISTENT_STORAGE_OVERWRITE: str
  UNZIP_TO_PERSISTENT_STORAGE_CLEAR_BEFORE: str
  LOCALSTORAGE_ZIP_FILENAME_PREFIX: str
  DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES: List[str]
  APPEND_TO_MAP_FILES_EVERY_X_LINES: int
  SECURITY_SCAN_SETTINGS_FILENAME: str
  DEFAULT_SECURITY_SCAN_SETTINGS: Dict[str, Any]



CRAWLER_HARDCODED_CONFIG = CrawlerHardcodedConfig(
  PERSISTENT_STORAGE_PATH_DOMAINS_SUBFOLDER="domains"
  ,PERSISTENT_STORAGE_PATH_SITES_SUBFOLDER="sites"
  ,PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER="crawler"
  ,PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER="jobs"
  ,PERSISTENT_STORAGE_PATH_TEMP_SUBFOLDER="_temp"
  ,PERSISTENT_STORAGE_PATH_DOCUMENTS_FOLDER="01_files"
  ,PERSISTENT_STORAGE_PATH_LISTS_FOLDER="02_lists"
  ,PERSISTENT_STORAGE_PATH_SITEPAGES_FOLDER="03_sitepages"
  ,PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER="01_originals"
  ,PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER="02_embedded"
  ,PERSISTENT_STORAGE_PATH_FAILED_SUBFOLDER="03_failed"
  ,PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE=5
  ,DOMAIN_JSON="domain.json"
  ,SITE_JSON="site.json"
  ,FILES_METADATA_JSON="files_metadata.json"
  ,SHAREPOINT_MAP_CSV="sharepoint_map.csv"
  ,SHAREPOINT_ERROR_MAP_CSV="sharepoint_error_map.csv"
  ,FILE_MAP_CSV="files_map.csv"
  ,FILE_FAILED_MAP_CSV="files_failed_map.csv"
  ,VECTOR_STORE_MAP_CSV="vectorstore_map.csv"
  ,UNZIP_TO_PERSISTENT_STORAGE_IF_NEWER=".unzip_to_persistant_storage_if_newer"
  ,UNZIP_TO_PERSISTENT_STORAGE_OVERWRITE=".unzip_to_persistant_storage_overwrite"
  ,UNZIP_TO_PERSISTENT_STORAGE_CLEAR_BEFORE=".unzip_to_persistant_storage_clear_before"
  ,LOCALSTORAGE_ZIP_FILENAME_PREFIX="download_"
  # https://platform.openai.com/docs/assistants/tools/file-search/supported-files#supported-files
  ,DEFAULT_FILETYPES_ACCEPTED_BY_VECTOR_STORES=["c", "cpp", "cs", "css", "doc", "docx", "go", "html", "java", "js", "json", "md", "pdf", "php", "pptx", "py", "rb", "sh", "tex", "ts", "txt"]
  ,APPEND_TO_MAP_FILES_EVERY_X_LINES=10
  ,SECURITY_SCAN_SETTINGS_FILENAME="security_scan_settings.json"
  ,DEFAULT_SECURITY_SCAN_SETTINGS={
    "do_not_resolve_these_groups": ["Everyone except external users"],
    "ignore_accounts": ["SHAREPOINT\\system", "app@sharepoint", "c:0!.s|windows"],
    "ignore_permission_levels": ["Limited Access"],
    "ignore_sharepoint_groups": [],
    "max_group_nesting_level": 5,
    "ignore_lists": [
      "Access Requests", "App Packages", "appdata", "appfiles", "Apps in Testing",
      "AuditLogs", "Cache Profiles", "Composed Looks", "Content and Structure Reports",
      "Content type publishing error log", "Converted Forms", "Device Channels",
      "Form Templates", "fpdatasources",
      "Get started with Apps for Office and SharePoint", "List Template Gallery",
      "Long Running Operation Status", "Maintenance Log Library", "Master Docs",
      "Master Page Gallery", "MicroFeed", "NintexFormXml", "Notification List",
      "Project Policy Item List", "Quick Deploy Items", "Relationships List",
      "Reporting Metadata", "Reporting Templates", "Reusable Content",
      "Search Config List", "Site Assets", "Site Collection Documents",
      "Site Collection Images", "Solution Gallery", "Style Library",
      "Suggested Content Browser Locations", "TaxonomyHiddenList", "Theme Gallery",
      "Translation Packages", "Translation Status", "User Information List",
      "Variation Labels", "Web Part Gallery", "wfpub", "wfsvc",
      "Workflow History", "Workflow Tasks"
    ],
    "fields_to_load": ["SharedWithUsers", "SharedWithDetails"],
    "ignore_fields": [
      "_CheckinComment", "_CommentCount", "_ComplianceFlags", "_ComplianceTag",
      "_ComplianceTagUserId", "_ComplianceTagWrittenTime", "_CopySource", "_DisplayName",
      "_dlc_DocId", "_dlc_DocIdUrl", "_ExtendedDescription", "_IsRecord", "_LikeCount",
      "_ModerationComments", "_ModerationStatus", "_UIVersionString", "Author",
      "AppAuthor", "AppEditor", "CheckoutUser", "ComplianceAssetId", "ContentType",
      "Created", "DocIcon", "Edit", "Editor", "FileSizeDisplay", "FileLeafRef",
      "FolderChildCount", "ID", "ItemChildCount", "Language", "LinkTitle",
      "LinkFilename", "LinkFilenameNoMenu", "MediaServiceAutoTags", "MediaServiceOCR",
      "MediaServiceKeyPoints", "Modified", "ParentVersionString", "PublishingStartDate",
      "PublishingExpirationDate", "ParentLeafName", "SharedWithUsers", "SharedWithDetails",
      "Tag", "Title"
    ],
    "output_columns": [
      "LoginName", "DisplayName", "Email", "PermissionLevel", "SharedDateTime",
      "SharedByDisplayName", "SharedByLoginName", "ViaGroup", "ViaGroupId",
      "ViaGroupType", "AssignmentType", "NestingLevel", "ParentGroup"
    ]
  }
)
