# Common functions for SharePoint operations using Office365-REST-Python-Client
# https://pypi.org/project/Office365-REST-Python-Client/#Working-with-SharePoint-API
from typing import Optional
from urllib.parse import urlparse
from dataclasses import asdict, dataclass
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list import List as DocumentLibrary

@dataclass
class SharePointFile:
    id: str
    unique_id: str
    filename: str
    file_leaf_ref: str
    server_relative_url: str
    file_size: int
    last_modified_utc: str
    last_modified_timestamp: int

def connect_to_site_using_client_id(site_url: str, client_id: str, client_secret: str) -> ClientContext:
  """
  Connect to a SharePoint site using client credentials (App-Only authentication).
  This method uses the client credentials flow (OAuth 2.0) to authenticate with SharePoint Online or SharePoint on-premises.
  
  Args:
    site_url: The SharePoint site URL (e.g., 'https://contoso.sharepoint.com/sites/mysite')
    client_id: The OAuth client ID of the registered application
    client_secret: The client secret associated with the application
    
  Returns:
    ClientContext: An authenticated SharePoint client context object
  """
  ctx = ClientContext(site_url).with_credentials(client_id=client_id, client_secret=client_secret)
  return ctx

def try_get_document_library(ctx: ClientContext, site_url: str, library_url_part: str) -> Optional[DocumentLibrary]:
  """
  Get a SharePoint document library by its server-relative URL.
  
  Args:
    ctx: An authenticated SharePoint client context
    site_url: The SharePoint site URL (e.g., 'https://contoso.sharepoint.com/sites/demosite')
    library_url_part: The URL part of the document library (e.g., '/Shared Documents')
    
  Returns:
    DocumentLibrary: The SharePoint list/document library object, or None if the operation fails
    
  Example:
    site_url = "https://contoso.sharepoint.com/sites/demosite"
    library_url_part = "/Shared Documents"
    # This will construct: "/sites/demosite/Shared Documents"
  """
  
  # Extract the site path from the site URL
  # e.g., 'https://contoso.sharepoint.com/sites/demosite' -> '/sites/demosite'
  parsed_url = urlparse(site_url)
  site_path = parsed_url.path.rstrip('/')
  
  # Ensure the library URL part starts with a forward slash
  if not library_url_part.startswith('/'): library_url_part = '/' + library_url_part
  
  # Construct the full server-relative URL
  # e.g., '/sites/demosite' + '/Shared Documents' = '/sites/demosite/Shared Documents'
  site_relative_url = site_path + library_url_part
  
  # Get the list (document library) by its server-relative URL
  try:
    document_library = ctx.web.get_list(site_relative_url).get().execute_query()
    return document_library
  except Exception as e:
    return None


def get_document_library_files(ctx: ClientContext, document_library: DocumentLibrary, filter: str, request_data: dict) -> list[SharePointFile]:
  """
  Get all files from a SharePoint document library, handling pagination automatically.
  
  This function retrieves ALL files from the library, even if there are more than 5000 items,
  by using the get_all() method which handles pagination internally.
  
  Args:
    ctx: An authenticated SharePoint client context
    document_library: The SharePoint document library object
    filter: Optional OData filter string (e.g., "FileLeafRef eq 'document.pdf'"). If None or empty, no filter is applied.
    request_data: Dictionary for logging output
    
  Returns:
    list[SharePointFile]: List of SharePointFile dataclass instances
    
  Example:
    filter = "FileLeafRef eq 'document.pdf'"  # Optional filter
    files = get_document_library_files(ctx, library, filter, request_data)
  """
  from utils import log_function_output
  from datetime import datetime
  
  try:
    log_function_output(request_data, f"Starting to retrieve files from document library: {document_library.properties.get('Title', 'Unknown')}")
    
    # Define progress callback for pagination
    def print_progress(items):
      """Callback function to track pagination progress"""
      log_function_output(request_data, f"Retrieved {len(items)} items so far...")
    
    # Build the query with optional filter
    # Select only file items (FileSystemObjectType = 0 means file, 1 means folder)
    items_query = document_library.items.select([
      "Id",
      "UniqueId", 
      "FileLeafRef",
      "FileRef",
      "File_x0020_Size",
      "Modified",
      "FileSystemObjectType"
    ]).filter("FileSystemObjectType eq 0")  # Only files, not folders
    
    # Apply additional filter if provided
    if filter and filter.strip():
      items_query = items_query.filter(filter)
      log_function_output(request_data, f"Applying filter: {filter}")
    
    # Use get_all() to retrieve all items with pagination (page size: 1000)
    # This method automatically handles the 5000 item limit by paginating
    page_size = 1000
    all_items = items_query.get_all(page_size, print_progress).execute_query()
    
    log_function_output(request_data, f"Total files retrieved: {len(all_items)}")
    
    # Convert to SharePointFile dataclass instances
    sharepoint_files = []
    for item in all_items:
      try:
        # Extract properties
        item_id = str(item.properties.get('Id', ''))
        unique_id = str(item.properties.get('UniqueId', ''))
        file_leaf_ref = item.properties.get('FileLeafRef', '')
        file_ref = item.properties.get('FileRef', '')
        file_size = int(item.properties.get('File_x0020_Size', 0))
        modified = item.properties.get('Modified', '')
        
        # Parse and format the modified date
        last_modified_utc = ''
        last_modified_timestamp = 0
        if modified:
          try:
            # SharePoint returns dates in ISO format
            dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
            last_modified_utc = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            last_modified_timestamp = int(dt.timestamp())
          except Exception as date_error:
            log_function_output(request_data, f"Warning: Failed to parse date for file {file_leaf_ref}: {date_error}")
            last_modified_utc = modified
            last_modified_timestamp = 0
        
        # Create SharePointFile instance
        sp_file = SharePointFile(
          id=item_id,
          unique_id=unique_id,
          filename=file_leaf_ref,
          file_leaf_ref=file_leaf_ref,
          server_relative_url=file_ref,
          file_size=file_size,
          last_modified_utc=last_modified_utc,
          last_modified_timestamp=last_modified_timestamp
        )
        sharepoint_files.append(sp_file)
        
      except Exception as item_error:
        log_function_output(request_data, f"Warning: Failed to process item: {item_error}")
        continue
    
    log_function_output(request_data, f"Successfully converted {len(sharepoint_files)} files to SharePointFile objects")
    return sharepoint_files
    
  except Exception as e:
    log_function_output(request_data, f"ERROR: Failed to retrieve files from document library: {str(e)}")
    return []