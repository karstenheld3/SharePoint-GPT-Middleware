# Common functions for SharePoint operations using Office365-REST-Python-Client
# https://pypi.org/project/Office365-REST-Python-Client/#Working-with-SharePoint-API
from typing import Optional
from urllib.parse import urlparse
from dataclasses import asdict, dataclass
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.lists.list import List as DocumentLibrary
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend

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

def connect_to_site_using_client_id(site_url: str, client_id: str, tenant_id: str, cert_path: str, cert_password: str) -> ClientContext:
  """
  Connect to a SharePoint site using certificate-based authentication (App-Only authentication).
  This method uses MSAL with certificate credentials to authenticate with SharePoint Online, which supports Sites.Selected permissions.
  
  Args:
    site_url: The SharePoint site URL (e.g., 'https://contoso.sharepoint.com/sites/mysite')
    client_id: The OAuth client ID of the registered application
    tenant_id: The Azure AD tenant ID
    cert_path: Path to the PFX certificate file
    cert_password: Password for the PFX certificate
    
  Returns:
    ClientContext: An authenticated SharePoint client context object
  """
  
  # Load and convert PFX to PEM format (required by with_client_certificate)
  with open(cert_path, 'rb') as f:
    pfx_data = f.read()
  
  # Extract private key and certificate from PFX
  private_key, certificate, _ = pkcs12.load_key_and_certificates(
    pfx_data,
    cert_password.encode() if cert_password else None,
    backend=default_backend()
  )
  
  # Create temporary PEM file
  pem_file = cert_path.replace('.pfx', '_temp.pem')
  with open(pem_file, 'wb') as f:
    # Write private key
    f.write(private_key.private_bytes(
      encoding=Encoding.PEM,
      format=PrivateFormat.PKCS8,
      encryption_algorithm=NoEncryption()
    ))
    # Write certificate
    f.write(certificate.public_bytes(Encoding.PEM))
  
  # Get certificate thumbprint
  thumbprint = certificate.fingerprint(certificate.signature_hash_algorithm).hex().upper()
  
  # Connect using certificate-based authentication
  # The library handles MSAL token acquisition internally
  ctx = ClientContext(site_url).with_client_certificate(
    tenant=tenant_id,
    client_id=client_id,
    thumbprint=thumbprint,
    cert_path=pem_file
  )
  return ctx

def try_get_document_library(ctx: ClientContext, site_url: str, library_url_part: str) -> tuple[Optional[DocumentLibrary], Optional[str]]:
  """
  Get a SharePoint document library by its server-relative URL.
  
  Args:
    ctx: An authenticated SharePoint client context
    site_url: The SharePoint site URL (e.g., 'https://contoso.sharepoint.com/sites/demosite')
    library_url_part: The URL part of the document library (e.g., '/Shared Documents')
    
  Returns:
    tuple: (DocumentLibrary or None, error_message or None)
      - If successful: (DocumentLibrary, None)
      - If failed: (None, error_message)
    
  Example:
    site_url = "https://contoso.sharepoint.com/sites/demosite"
    library_url_part = "/Shared Documents"
    # This will construct: "/sites/demosite/Shared Documents"
    
    library, error = try_get_document_library(ctx, site_url, library_url_part)
    if library:
      # Success
    else:
      # Failed, error contains the message
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
    return document_library, None
  except Exception as e:
    error_message = f"Failed to get document library at '{site_relative_url}': {str(e)}"
    return None, error_message


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